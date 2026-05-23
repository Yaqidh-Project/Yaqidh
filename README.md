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
* **Real-Time Fall Detection** - Identifies falls instantly using ONNX-optimized models
* **Violence/Aggression Detection** - Detects physical aggression between children or staff
* **Confidence-Based Incident Classification** - Categorizes incidents as Critical (≥75% confidence) or Warning (<75%)
* **Smart Notification Throttling** - Prevents alert fatigue with intelligent cooldown mechanisms

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
* **Incident Status Tracking** - Manage incident lifecycle from detection to resolution

### 📈 Analytics & Reporting
* **Dashboard Analytics** - Real-time KPIs and trend indicators
* **Advanced Reports** - Generate customizable reports with date ranges, category filters, and export options
* **Incident Trend Charts** - Visualize incident patterns over time
* **Category Breakdown Analysis** - Understand fall vs. violence detection distribution

### 🔐 Authentication & Authorization
* **JWT-Based Authentication** - Secure access tokens (15-min expiry) and refresh tokens (7-day expiry)
* **Role-Based Access Control (RBAC)** - Three distinct roles with granular permissions (Manager, Teacher, Parent)
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
* **Models:** YOLO-based ONNX models (fall_detection.onnx, violence_detection.onnx)
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
* Node.js (v16+)
* npm (v8+)

### Steps
1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/AliyahAlabdali/yaqidh.git]\   cd yaqidh
    ```

2.  **Install Frontend Dependencies**
    ```bash
    npm install
    ```

3.  **Run the Development Server**
    ```bash
    npm run dev
    ```
    The application will launch at `https://yaqidh.vercel.app/login`.

---

## 📂 Project Structure

```text
Yaqidh/
├── Models/
│   ├── Yaqidh_Fall_Model.ipynb
│   ├── best.pt
│   ├── Yaqidh_Violence_Model.ipynb
│   └── Violence_best.pt
├── public/
│   ├── Yaqidh-logo.png
│   └── vite.svg
├── src/
│   ├── assets/
│   │   └── react.svg
│   ├── components/
│   │   └── Layout.jsx
│   ├── pages/
│   │   ├── About.jsx
│   │   ├── Dashboard.jsx
│   │   ├── ForgotPassword.jsx
│   │   ├── Incidents.jsx
│   │   ├── LiveMonitor.jsx
│   │   ├── LiveMonitoring.jsx
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Reports.jsx
│   │   └── Settings.jsx
│   ├── App.jsx
│   ├── App.css
│   ├── main.jsx
│   └── index.css
├── .gitignore
├── README.md
├── eslint.config.js
├── index.html
├── package-lock.json
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── vercel.json
└── vite.config.js
