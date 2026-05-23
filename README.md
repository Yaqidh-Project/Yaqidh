# Yaqidh | يقظ
### Smart Vision System for Safer Childhood Environments

![Project Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-Academic-green)

> **Project ID:** CSAI-471-P1-F09\
> **Institution:** Umm Al-Qura University - Faculty of Computer and Information Systems\
> **Department:** Department of Computer Science and Artificial Intelligence

---

## 📖 Overview

**Yaqidh** is a comprehensive AI-powered child safety monitoring system designed for nurseries, daycare centers, and home environments. The system autonomously detects critical incidents specifically **Falls** and **Physical Violence** using YOLO8s ONNX-based models. It provides real-time alerts to caregivers and administrators, drastically reducing response times to emergencies and enhancing overall child safety.

This solution aims to reduce the reliance on continuous manual surveillance, minimize response times to accidents, and provide peace of mind to parents and staff.

## ✨ Key Features

### 🤖 AI Detection System
* **Real-Time Fall Detection** - Identifies falls instantly using YOLO8s ONNX optimized model
* **Real-Time Violence Detection** - Detects physical violence between children using YOLO8s ONNX optimized model
* **Confidence-Based Incident Classification** - Categorizes incidents as Critical (≥75% confidence) or Warning (<75%)
* **Smart Notification Throttling** - Prevents alert spamming with intelligent cooldown mechanisms

### 🎯 Role-Based Dashboard
* **Manager Dashboard** - System overview with KPIs, incident summaries, and zone/camera management
* **Teacher Incident Tracking** - Simplified interface for logging and viewing incidents in assigned zones
* **Parent Portal** - Access to reports and incident history for their child's assigned zones

### 🔔 Intelligent Alerting
* **Real-Time WebSocket Notifications** - Instant alerts to connected users via real-time event streaming
* **Multi-Channel Notifications** - SMS and email alerts for critical incidents
* **Per-User Notification Preferences** - Customizable notification channels and preferences
* **Incident Cooldown Management** - Prevents duplicate alerts within cooldown windows (20s for falls, 40s for violence)

### 📊 Comprehensive Incident Management
* **Incident Logging & Storage** - Auto-generated incident records with video clips
* **Video Clip Archival** - Automatic storage and retrieval of incident footage
* **Advanced Filtering & Search** - Filter incidents by type, date range, severity, and location

### 📈 Analytics & Reporting
* **Dashboard Analytics** - Real-time KPIs and trend indicators
* **Advanced Reports** - Generate customizable reports with date ranges, category filters, and export options
* **Incident Trend Charts** - Visualize incident patterns over time
* **Category Breakdown Analysis** - Understand fall vs. violence detection distribution

### 🔐 Authentication & Authorization
* **JWT-Based Authentication** - Secure access tokens (15-min expiry) and refresh tokens (7-day expiry)
* **Role-Based Access Control (RBAC)** - Three distinct roles with granular permissions (Manager, Teacher, Parent/Caregiver)
* **Phone Verification (2FA)** - OTP-based phone verification for enhanced security
* **Zone-Based Data Isolation** - Users can only access incidents and resources within their assigned zones

### 🎥 Live Monitoring
* **Real-Time Video Feed Control** - View live camera streams with power on/off functionality
* **On-Screen Display (OSD)** - Timestamp, latency, and analysis status overlays
* **Stream Status Indicators** - Real-time LIVE/STANDBY badges and network quality indicators

### ⚙️ Administration & Configuration
* **User Management** - Create, edit, and manage staff and parent accounts
* **Zone Management** - Define and organize monitoring zones
* **Camera Configuration** - Add, edit, and manage camera streams with zone assignments
* **Notification Preferences** - Configure SMS, email, and push notification settings

## 🛠️ Technology Stack

### Frontend
* **Framework:** React 19 with Vite
* **Styling:** Tailwind CSS 4 with custom theming
* **Routing:** React Router DOM 7
* **Charts & Visualization:** Recharts
* **Icons:** Lucide React
* **Video Handling:** React Webcam for live feeds

### Backend
* **Framework:** FastAPI (async-first Python web framework)
* **Server:** Uvicorn (ASGI server)
* **Database:** PostgreSQL with SQLAlchemy async ORM
* **Migrations:** Alembic for schema management
* **Authentication:** JWT (HS256) with bcrypt password hashing
* **AI/ML:** ONNX Runtime for model inference
* **Real-Time Communication:** WebSockets for live notifications
* **Task Scheduling:** APScheduler for retention cleanup

### AI & Computer Vision
* **Models:** YOLO8-based ONNX models (fall_detection.onnx, violence_detection.onnx)
* **Inference Engine:** ONNX Runtime
* **Preprocessing:** OpenCV for image/video processing
* **Model Training:** Goggle Colab - view notebooks in `notebooks/`

### Infrastructure
* **Database:** PostgreSQL with async driver (asyncpg)
* **File Storage:** Local disk storage for incident clips (configurable retention: 30 days)
* **Deployment:** Docker-ready with environment-based configuration

---

## 🚀 Installation & Setup

### Prerequisites

**Backend:**
* Python 3.9+
* pip or virtual environment manager (venv/conda)
* PostgreSQL 12+

**Frontend:**
* Node.js 16+
* npm 8+

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/yaqidh
   SECRET_KEY=your-super-secret-key-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=15
   REFRESH_TOKEN_EXPIRE_DAYS=7
   CLIP_RETENTION_DAYS=30
   CONFIDENCE_THRESHOLD=0.7
   VIOLENCE_CONFIDENCE_THRESHOLD=0.4
   PORT=8000
   ```

5. **Setup database:**
   ```bash
   python -m alembic upgrade head
   ```

6. **Start backend server:**
   ```bash
   bash start.sh
   # or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Backend will be available at `http://localhost:8000/docs` (Swagger UI)

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```
   Frontend will be available at `http://localhost:5173`

4. **Build for production:**
   ```bash
   npm run build
   ```
   Generates optimized build in `dist/`

---

## 📂 Project Structure

```
Yaqidh/
├── backend/                          # FastAPI Python backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app initialization
│   │   ├── config.py                # Environment & settings
│   │   ├── database.py              # SQLAlchemy async setup
│   │   ├── auth/
│   │   │   ├── jwt.py              # JWT token creation/validation
│   │   │   └── dependencies.py     # Auth dependency injection
│   │   ├── models/                 # Database ORM models
│   │   │   ├── user.py            # User model (roles, zones, notifications)
│   │   │   ├── zone.py            # Zone model (grouping cameras & users)
│   │   │   ├── camera.py          # Camera model (video sources)
│   │   │   ├── incident.py        # Incident model (detected events)
│   │   │   ├── report.py          # Report model (analytics)
│   │   │   ├── phone_code.py      # Phone verification OTP codes
│   │   │   └── enums.py           # Role, category, incident type enums
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── routers/                # API endpoint handlers
│   │   │   ├── auth.py            # Registration, login, phone verification
│   │   │   ├── users.py           # User CRUD & profile management
│   │   │   ├── zones.py           # Zone CRUD & user assignment
│   │   │   ├── cameras.py         # Camera CRUD & configuration
│   │   │   ├── incidents.py       # Incident CRUD & filtering
│   │   │   ├── reports.py         # Report generation & analytics
│   │   │   ├── inference.py       # AI model inference endpoints
│   │   │   ├── websocket.py       # WebSocket notifications
│   │   │   ├── clips.py           # Video clip streaming
│   │   │   └── manager.py         # Manager-specific operations
│   │   └── services/               # Business logic & AI
│   │       ├── inference.py       # ONNX model loading & prediction
│   │       ├── notifications.py   # WebSocket manager & cooldown logic
│   │       └── retention.py       # Clip retention cleanup task
│   ├── alembic/                    # Database migrations
│   │   ├── versions/
│   │   │   ├── 0001_initial_schema.py              # Core tables
│   │   │   ├── 0002_security_enhancements.py       # Phone verification
│   │   │   └── 0003_type_safety_and_schema.py      # Type improvements
│   │   └── env.py                 # Migration environment config
│   ├── incident_clips/             # Stored video clips
│   ├── models/                     # ONNX model weights
│   │   ├── fall_detection.onnx
│   │   └── violence_detection.onnx
│   ├── requirements.txt            # Python dependencies
│   ├── start.sh                    # Backend startup script
│   └── README.md                   # Backend documentation
│
├── frontend/                        # React + Vite web application
│   ├── src/
│   │   ├── App.jsx                # Main router & auth wrapper
│   │   ├── main.jsx               # React entry point
│   │   ├── App.css                # Global styles
│   │   ├── index.css              # Base styles
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx      # Manager/Parent dashboard overview
│   │   │   ├── LiveMonitoring.jsx # Real-time video feed control
│   │   │   ├── Incidents.jsx      # Incident log & viewer
│   │   │   ├── Reports.jsx        # Analytics & reporting dashboard
│   │   │   ├── Settings.jsx       # Profile, notifications, user/camera management
│   │   │   ├── Login.jsx          # Authentication form
│   │   │   ├── Register.jsx       # User registration (2-step)
│   │   │   ├── ForgotPassword.jsx # Password reset request
│   │   │   └── About.jsx          # System information page
│   │   ├── components/
│   │   │   └── Layout.jsx         # Sidebar navigation & app shell
│   │   └── assets/                # Images, icons, etc.
│   ├── package.json               # Node.js dependencies
│   ├── vite.config.js             # Vite build configuration
│   ├── tailwind.config.js         # Tailwind CSS theming
│   ├── postcss.config.js          # PostCSS configuration
│   ├── index.html                 # HTML entry point
│   └── README.md                  # Frontend documentation
│
├── notebooks/                      # AI Model Training
│   ├── fall model/
│   │   ├── Yaqidh_Fall_Detection_Model.ipynb
│   │   └── fall_best.pt           # PyTorch model checkpoint
│   └── violence model/
│       ├── Yaqidh_Violence_Detection_Model.ipynb
│       └── violence_best.pt       # PyTorch model checkpoint
│
├── tests/                         # Integration tests
│   └── parallel_detection_test/
│       ├── test_realtime_camera.py
│       └── INTEGRATION_TESTING.md
│
└── README.md                      # This file
```
