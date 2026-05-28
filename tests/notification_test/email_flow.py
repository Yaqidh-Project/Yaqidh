"""
Yaqidh Email Notification Test Script

This script tests the complete email notification flow:
1. Register a test user
2. Login to get JWT token
3. Get or automatically create a valid camera from database
4. Use a REAL training image (danger_test.jpg) to trigger YOLOv8 detection
5. Send incident detection to trigger email notification
6. Report results
"""

from pathlib import Path
from dotenv import load_dotenv
# Force loading the correct .env file from the backend folder
base_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=base_dir / "backend" / ".env")

import asyncio
import httpx
import json
import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.camera import Camera
from app.models.zone import Zone

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test_manager@gmail.com"
TEST_PASSWORD = "SecureTest@123456"
TEST_FULL_NAME = "Test Manager"
TEST_PHONE = "0501234567"
RECIPIENT_EMAIL = "rawan.jalahmadi@gmail.com"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(title: str):
    width = 60
    print(f"\n{BOLD}{BLUE}{'=' * width}{RESET}")
    print(f"{BOLD}{BLUE}{title.center(width)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * width}{RESET}\n")


def print_step(step_num: int, title: str):
    print(f"{BOLD}{YELLOW}STEP {step_num}: {title}{RESET}")


def print_success(message: str, detail: str = ""):
    detail_str = f" → {detail}" if detail else ""
    print(f"{GREEN}✅ {message}{detail_str}{RESET}")


def print_error(message: str, detail: str = ""):
    detail_str = f" → {detail}" if detail else ""
    print(f"{RED}❌ {message}{detail_str}{RESET}")


def print_info(message: str, detail: str = ""):
    detail_str = f": {detail}" if detail else ""
    print(f"{BLUE}ℹ️  {message}{detail_str}{RESET}")


async def step_1_register_user(client: httpx.AsyncClient) -> Optional[str]:
    print_step(1, "Registering Test User")
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_FULL_NAME,
        "phone_number": TEST_PHONE,
        "role_name": "Manager",
    }
    try:
        response = await client.post(f"{BASE_URL}/auth/register", json=payload)
        if response.status_code == 201:
            data = response.json()
            return data.get("user_id")
        elif response.status_code in (409, 400):
            print_info("User already exists - continuing with login")
            return "existing"
        return None
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return None


async def step_2_login_user(client: httpx.AsyncClient) -> Optional[str]:
    print_step(2, "Logging In")
    payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    try:
        response = await client.post(f"{BASE_URL}/auth/login", json=payload)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print_success(f"Status: {response.status_code}")
            print_success(f"Token acquired: {token[:30]}...")
            return token
        return None
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return None


async def step_3_get_camera() -> Optional[tuple[str, str]]:
    print_step(3, "Getting Camera ID from Database")
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Camera).join(Zone).limit(1))
            camera = result.scalar_one_or_none()
            
            if camera:
                print_success(f"Status: Success (Found Existing)")
                print_success(f"Camera ID: {camera.camera_id}")
                return str(camera.camera_id), camera.camera_name
            
            print_info("No cameras found. Auto-generating a test camera and zone")
            zone_result = await db.execute(select(Zone).limit(1))
            zone = zone_result.scalar_one_or_none()
            
            if not zone:
                zone = Zone(zone_id=uuid.uuid4(), zone_name="Main Daycare Zone")
                db.add(zone)
                await db.flush()
            
            new_camera = Camera(
                camera_id=uuid.uuid4(),
                camera_name="Test Camera 01",
                camera_type="IP",
                stream_url="rtsp://localhost:8554/live",
                ip_address="127.0.0.1",
                status="Active",
                zone_id=zone.zone_id
            )
            db.add(new_camera)
            await db.commit()
            await db.refresh(new_camera)
            return str(new_camera.camera_id), new_camera.camera_name
    except Exception as e:
        print_error(f"Exception during DB operation: {str(e)}")
        return None


async def step_4_create_test_image() -> Optional[Path]:
    print_step(4, "Loading Real Threat Test Image")
    
    script_dir = Path(__file__).parent
    image_path = script_dir / "danger_test.jpg"
    
    if image_path.exists():
        file_size = image_path.stat().st_size
        print_success("Real test image found!", f"File: {image_path.name} ({file_size} bytes)")
        return image_path
    else:
        print_error(f"Could not find '{image_path.name}' in the script directory!")
        print_info(f"Expected path: {image_path.absolute()}")
        return None


async def step_5_send_incident(
    client: httpx.AsyncClient,
    token: str,
    camera_id: str,
    image_path: Path
) -> Optional[str]:
    print_step(5, "Sending Incident Detection")
    try:
        with open(image_path, 'rb') as f:
            files = {
                'frame': (image_path.name, f, 'image/jpeg'),
                'camera_id': (None, camera_id),
            }
            headers = {'Authorization': f'Bearer {token}'}
            
            response = await client.post(
                f"{BASE_URL}/inference/detect",
                files=files,
                headers=headers,
            )
        
        if response.status_code == 200:
            data = response.json()
            incident_created = data.get("incident_created", False)
            incidents = data.get("incidents", [])
            
            print_success(f"Status: {response.status_code}")
            print_success(f"Incident Created: {incident_created}")
            
            if incident_created and incidents:
                incident_id = incidents[0].get("incident_id")
                print_success(f"Incident ID: {incident_id}")
                print_success(f"Type: {incidents[0].get('incident_type')}")
                print_success(f"Confidence: {incidents[0].get('confidence', 0) * 100:.1f}%")
                return incident_id
            elif incident_created:
                return "success_without_list"
            
            print_error("YOLO Model processed the image but detected NO incident. (Incident Created: False)")
            return None
        else:
            print_error(f"Status: {response.status_code}", response.text)
            return None
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return None


async def main():
    print_header("YAQIDH EMAIL NOTIFICATION TEST")
    async with httpx.AsyncClient(timeout=45.0) as client:
        if await step_1_register_user(client) is None: return False
        
        token = await step_2_login_user(client)
        if token is None: return False
        
        camera_data = await step_3_get_camera()
        if camera_data is None: return False
        camera_id, _ = camera_data
        
        image_path = await step_4_create_test_image()
        if image_path is None: return False
        
        incident_id = await step_5_send_incident(client, token, camera_id, image_path)
        if incident_id is None: return False
    
    print_header("TEST RESULTS")
    print(f"{GREEN}{BOLD}Base API Test State: SUCCESS (Incident Triggered!){RESET}\n")
    print_success("Email Notification: TRIGGERED")
    print_info("Recipient", RECIPIENT_EMAIL)
    return True

if __name__ == "__main__":
    asyncio.run(main())