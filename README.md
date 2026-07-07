# ⚡ PowerCortex: Smart Grid Intelligence Platform

PowerCortex is a production-grade utility operations platform designed for smart grids. It provides real-time demand forecasting, energy theft and anomaly detection, and ML-powered transformer health monitoring. The system is architected with a high-performance **FastAPI backend** optimized for speed and a responsive **Flutter frontend** built for web, desktop, and mobile environments.

---

## 🏗️ System Architecture

The following diagram illustrates the PowerCortex system architecture, highlighting the flow of data from the Flutter client through the FastAPI API gateways down to the ML analysis models and MongoDB data store:

```mermaid
graph TD
    subgraph Client Layer (Flutter)
        A[Mobile Client]
        B[Web Client]
        C[Desktop Client]
    end

    subgraph API Gateway / Backend (FastAPI)
        D[Version Rewrite Middleware]
        E[Rate Limiter & CORS]
        F[Auth Router]
        G[Analytics / Operations Routers]
    end

    subgraph Services & ML Layer
        H[Auth Service]
        I[Email / 2FA Service]
        J[Forecasting Service <br/> LSTM Model]
        K[Theft Detection Service]
        L[Transformer Health Service]
    end

    subgraph Persistence Layer
        M[(MongoDB Database)]
    end

    A & B & C -->|REST API| D
    D --> E
    E --> F & G
    F --> H
    H -->|2FA / Resets| I
    G --> J & K & L
    H & J & K & L --> M
```

---

## 🚀 Key Features

* **Real-Time Forecasting:** Leverages LSTM neural networks to provide granular, region-based demand forecasting.
* **Transformer Health Monitoring:** Tracks equipment lifecycle metrics, logs maintenance schedules, and flags thermal/voltage anomalies.
* **Theft & Anomaly Detection:** Identifies erratic consumption patterns to isolate power theft in real time.
* **Dual-Layer Authentication:** Secure JWT-based session management, audit log tracking, and email-based Multi-Factor Authentication (2FA).
* **Enterprise Grade Security:** Includes rate limiting, CORS origin enforcement, hidden variables, and automatic route rewrites to support legacy API versions.
* **Scalability:** Optimized with asynchronous DB drivers (Motor) and built-in database indexing, load-tested to handle 5,000+ concurrent operators.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | Flutter (Dart) | Single-codebase responsive UI supporting Android, iOS, Web, and Windows Desktop. |
| **Backend** | Python 3.12, FastAPI, Uvicorn | Async web framework optimized for high-throughput operational dashboards. |
| **Database** | MongoDB | Document database utilized for high-velocity IoT telemetry data. |
| **Database Driver** | Motor (Async PyMongo) | Asynchronous MongoDB driver for non-blocking I/O operations. |
| **Machine Learning** | Keras / TensorFlow, Pandas | Powers the LSTM forecasting model and anomaly classification algorithms. |
| **Load Testing** | Locust | Stress testing suite to validate endpoint latency under heavy swarms. |

---

## 📂 Project Structure

```
├── android/                   # Android native project files
├── ios/                       # iOS native project files
├── lib/                       # Flutter Application Codebase
│   ├── core/                  # Global controllers, styles, themes, and API clients
│   └── features/              # Feature-oriented UI and Business Logic modules (Auth, KPI)
├── backend/                   # FastAPI Backend Service
│   ├── app/                   # App root
│   │   ├── core/              # Config layers, database connections, and JWT validation
│   │   ├── middleware/        # Request logs and version rewrite layers
│   │   ├── models/            # Pre-loaded ML models
│   │   ├── repositories/      # Data access layer (MongoDB CRUD)
│   │   ├── routers/           # API endpoints (Auth, Forecasts, Transformers)
│   │   ├── services/          # Core business services
│   │   └── utils/             # Helper utilities, strength validation, and timezone-naive helpers
│   └── tests/                 # Backend API and unit test suites
├── docker-compose.yml         # Multi-container production compose configuration
└── locustfile.py              # Performance load testing script
```

---

## ⚙️ Local Development Setup

### 1. Database & Environment
1. Ensure you have MongoDB running locally on `mongodb://localhost:27017`.
2. Navigate to the `backend/` directory, copy `.env.example` to `.env`, and populate your secrets:
   ```env
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=powercortex
   JWT_SECRET_KEY=your_secure_jwt_secret
   JWT_REFRESH_SECRET=your_secure_refresh_secret
   DEBUG=true
   ```

### 2. Start the Backend API (FastAPI)
Activate your Python environment, install dependencies, and start the development server:
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*The interactive Swagger documentation will be available at `http://127.0.0.1:8000/docs`.*

### 3. Start the Frontend (Flutter)
Compile and launch the Flutter application (use `-d` to launch directly on your preferred target):
```bash
flutter pub get
flutter run -d windows    # Or: chrome, edge, <device-id>
```

---

## 🧪 Testing & Verification

### Run Automated Tests
PowerCortex includes unit and integration tests covering security, forecasting, and data ingestion.
```bash
cd backend
python -m pytest
```

### Run API Authentication Audits
Verify that endpoints are securely locked down and reject unauthorized requests:
```bash
python backend/tests/api_auth_test.py
```

### Load Testing (Stress Simulation)
To simulate concurrent smart grid operators:
```bash
locust -f locustfile.py
```
Open your browser at `http://localhost:8089` to control and swarm the endpoints.

---

## 📦 Production Deployment

### Option A: Docker Compose (Single-Server)
Build and spin up the complete multi-container stack in the background:
```bash
docker compose up -d --build
```
*This deploys MongoDB, runs database indexing, and exposes the FastAPI service on port `8000`.*

### Option B: Kubernetes (Scaling & Cloud Deployment)
Production K8s manifests are located under [backend/k8s/](file:///c:/Flutter/guvnl_project/backend/k8s). Apply the configurations in the following order:
```bash
# 1. Namespace
kubectl apply -f backend/k8s/namespace.yaml

# 2. ConfigMaps and Secrets
kubectl apply -f backend/k8s/configmap.yaml

# 3. MongoDB State
kubectl apply -f backend/k8s/mongodb-deployment.yaml

# 4. API Deployment
kubectl apply -f backend/k8s/fastapi-deployment.yaml

# 5. Horizontal Pod Autoscaler (Auto-scaling)
kubectl apply -f backend/k8s/fastapi-hpa.yaml
```

---

## 🔒 Security Standards

* **Credential Protection:** High-entropy JWT tokens with short expiration times. Refresh tokens are persisted in MongoDB and can be instantly revoked.
* **Audit Logging:** Every critical administrative action (password resets, 2FA configurations, maintenance updates) is logged with timestamp, user ID, and IP address.
* **Rate Limiting:** Protects endpoints against brute-force attacks via `slowapi` throttling middleware.
* **Heuristic Failbacks:** In production, AI-model fallbacks are restricted (`ALLOW_MODEL_FALLBACKS=False`) to ensure utility dashboard decisions are strictly backed by live model inferences.
