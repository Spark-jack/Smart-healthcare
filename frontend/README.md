# Smart Healthcare Frontend Portal

> ⚠️ **MEDICAL DISCLAIMER**: This application is a technological demonstration prototype and is NOT a certified medical device.

The frontend is built with **React 18**, **Vite**, **Tailwind CSS**, and **Recharts**. It provides dedicated clinical workflows for Patients, Physicians, and System Administrators.

---

## Features & Interfaces

1. **Patient Dashboard (`src/pages/PatientDashboard.jsx`)**:
   - Cardiometabolic risk overview cards displaying calibrated disease probabilities and 95% plausible uncertainty ranges.
   - Interactive SHAP factor waterfall charts highlighting top biomarker risk drivers.
   - Multi-step clinical intake survey modal with live BMI calculation.
   - Priority appointment booking with automatic triage urgency stamping.
2. **Physician Clinical Console (`src/pages/DoctorDashboard.jsx`)**:
   - Real-time `HIGH_RISK_FLAG` critical patient alert banner.
   - Triage queue prioritized by urgency scores and ML risk levels.
   - Comprehensive Patient Deep-Dive modal with longitudinal trajectory charts.
   - **Population Health Trends**: SQL-aggregated longitudinal line charts of risk over time, stacked bar charts of triage tiers, and demographic filter controls (age cohorts and sex).
3. **Administrator Console (`src/pages/AdminDashboard.jsx`)**:
   - System operational metrics and active user rollups.
   - **ML Pipeline & Model Calibration Audit**: Live telemetry displaying dataset source tags (`real`), held-out test AUC-ROC, accuracy, Expected Calibration Error (ECE), and sample counts.
   - Privileged account provisioning modal for authorized creation of doctors and admins.
   - Role management with safeguards preventing administrator self-demotion or self-deactivation.
4. **Persistent Notification Center (`src/components/common/Navbar.jsx`)**:
   - Bell icon with unread count badge.
   - 30-second polling interval for real-time triage flags, appointment confirmations, and reminders.
   - Dropdown panel supporting mark-as-read and mark-all-read operations.

---

## Setup & Running

```bash
# Install dependencies
npm install

# Run Vite development server
npm run dev

# Run production build validation
npm run build
```
