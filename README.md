# ⚡ PowerCortex: Smart Grid Intelligence Platform

**PowerCortex** is a production-grade utility operations platform for smart grids, delivering real-time demand forecasting, anomaly/theft detection, and ML-powered transformer health monitoring. It consists of a **FastAPI backend** optimized for speed and a **Flutter frontend** built for cross-platform deployment.

---

## 🚀 Key Features
- **Real-Time Forecasting:** Predict grid demand utilizing AI/ML models with granular, region-based analytics.
- **Equipment Health Monitoring:** Track transformer lifecycles, maintenance schedules, and voltage anomalies.
- **Theft & Anomaly Detection:** Instantly isolate erratic consumption patterns to identify energy theft.
- **Production Secure:** Fully audited API architecture with JWT authentication, hidden variables, and zero ghost-data fallbacks.
- **High-Performance Architecture:** Capable of scaling to thousands of concurrent utility operators, tested up to 5,000+ users via Locust.

---

## 🏗️ Architecture Stack
* **Frontend:** Flutter (iOS, Android, Web, Desktop)
* **Backend:** Python 3.12, FastAPI, Uvicorn
* **Database:** MongoDB (Motor Async Driver)
* **Load Testing:** Locust
* **AI/ML Integration:** Keras / TensorFlow, Pandas

---

## ⚙️ Local Development Setup

### 1. Database & Environment
1. Install MongoDB and ensure it is running on `mongodb://localhost:27017`.
2. Create a `.env` file in the `backend/` directory with your secrets:
   ```env
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DB_NAME=powercortex_db
   SECRET_KEY=your_secure_jwt_secret
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

### 2. Start the Backend (FastAPI)
Navigate to the backend directory, install the dependencies, and run the Uvicorn server:
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
*The API will be available at `http://127.0.0.1:8000/api/v1`*

### 3. Start the Frontend (Flutter)
Open a new terminal, navigate to the project root, and run the Flutter app:
```bash
flutter pub get
flutter run
```

---

## 🧪 Testing & Verification

**Authentication Audit:**
To test API lockdown and ensure JWT protection is enforced on all critical endpoints:
```bash
python backend/tests/api_auth_test.py
```

**Load Testing (Stress Testing):**
To simulate a massive influx of concurrent Smart Grid operators:
```bash
locust -f locustfile.py
```
Open `http://localhost:8089` to configure and launch the swarm.

---

## 🔒 Security & Optimization
* **Database Optimization:** Execute `python backend/app/core/database_indexes.py` on a fresh deployment to generate optimized MongoDB indices.
* **Model Fallbacks:** By default, model heuristic fallbacks are disabled in production (`ALLOW_MODEL_FALLBACKS=False`) to ensure 100% data integrity.

---

*Built with ❤️ for a smarter, greener grid.*
