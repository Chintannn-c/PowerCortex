# PowerCortex – AI-Powered Power Network Analytics Platform
## UI/UX Design Specification

**Version:** 1.0

---

# 1. Project Overview

**PowerCortex** is a modern, AI-powered power network analytics platform designed to help utility operators monitor, analyze, predict, and optimize electricity network operations. By blending machine learning predictions, real-time power network telemetry, and conversational AI-driven insights, PowerCortex empowers decision-makers to reduce operational losses, mitigate risk, and boost grid reliability.

The user interface resembles a professional enterprise utility operations center while maintaining a clean, responsive, and data-first software-as-a-service (SaaS) experience.

---

# 2. Design Goals

* **Clean and Professional Interface:** Suitable for industrial control rooms, utility engineers, and grid operators.
* **Data-First Dashboard Experience:** Critical metrics, active grid anomalies, and prediction confidences are always visible at a glance.
* **Fast Navigation:** Flat menu hierarchy ensuring operators reach any core page or diagnostic report within 2–3 taps.
* **Responsive Layout:** Dynamic UI adaptation supporting Mobile, Tablet, Desktop, and Ultrawide displays.
* **Modern SaaS Aesthetics:** Elegant grids, clean borders, glassmorphic touches, and clear typography.
* **Minimal Animations:** Only purposeful, non-distracting UI motions to maintain high focus in operations.
* **Complete Dark Mode:** Dedicated low-light visual themes to reduce operator eye fatigue during night shifts.
* **Enterprise-Grade Visualizations:** Rich, interactive charts displaying actual vs. predicted timelines.

---

# 3. Design Inspiration

* **Microsoft Power BI:** Comprehensive enterprise analytical widgets and layout blocks.
* **Grafana:** High-density real-time system monitoring and telemetry curves.
* **Google Cloud Console:** Structured, clean navigation rails and resource administration dashboards.
* **Utility Control Centers:** High-contrast indicator boards used in national electricity grids.
* **Industrial Monitoring Dashboards:** Direct, tabular, and compartmentalized representation of physical assets.

---

# 4. Color Palette

## Primary Colors

| Color Name | Hex Code | Visual Application / Context |
| :--- | :--- | :--- |
| **Primary Blue** | `#1E3A8A` | Main theme color, App Bar background, primary buttons |
| **Dark Blue** | `#0F172A` | Side navigation backgrounds, panel headers, core body text |
| **Light Blue** | `#DBEAFE` | Highlighting cards, secondary badges, active navigation selection |

---

## Status Colors

| Status | Hex Code | Color | Application / Trigger Condition |
| :--- | :--- | :--- | :--- |
| **Healthy** | `#22C55E` | Green | Safe load capacity, healthy asset score, offline anomaly triggers |
| **Warning** | `#F59E0B` | Amber | Minor load peaks, elevated transformer temperatures, pending audits |
| **Critical** | `#EF4444` | Red | Active grid faults, high-risk assets, theft detection flags |
| **Information**| `#3B82F6` | Blue | Telemetry log details, standard reports, standard AI updates |

---

## Background Colors

### Light Mode
* **Background:** `#F8FAFC`
* **Cards & Containers:** `#FFFFFF`
* **Text / Primary Elements:** `#0F172A`

### Dark Mode
* **Background:** `#0B1220`
* **Cards & Containers:** `#111827`
* **Text / Primary Elements:** `#F8FAFC`

---

# 5. Typography

* **Font Family:** `Poppins`
* **Fallback Font:** `Roboto`

## Text Styles

| Style | Size | Weight | Application |
| :--- | :--- | :--- | :--- |
| **Heading 1** | `32px` | Bold | Splash screens, main system module titles |
| **Heading 2** | `24px` | SemiBold | Section titles, interactive modal headers, big numbers |
| **Heading 3** | `20px` | Medium | Card titles, minor alert categories, dialog frames |
| **Body** | `14px` | Regular | Readout logs, data tables, chat assistant conversations |
| **Caption** | `12px` | Regular | Confidence scores, timestamps, card subtitles, axis labels |

---

# 6. Navigation Structure

```text
Splash Screen
      │
Login Screen
      │
Dashboard (Main Command Center)
      ├── Forecasting
      ├── Asset Monitoring
      ├── Fault & Theft Detection
      ├── AI Assistant
      ├── Reports & Analytics
      ├── System Health
      └── Settings
```

---

# 7. Application Pages (10 Screens)

### [1] Splash Screen
* **Purpose:** App initial boot, startup, and branding validation.
* **Core Components:**
  * Double lightning bolt **PowerCortex Logo** centered in the screen.
  * Sleek linear loading indicator.
  * Tagline: *"AI-Powered Power Network Analytics Platform"*
* **Aesthetics:** Styled with a premium dark blue gradient (`#0B1220` to `#1E3A8A`).
* **Animations:** 300ms smooth Fade In and gentle Logo Scale loading transition.
* **Startup Duration:** **2 Seconds** before routing to authentication.

### [2] Login Screen
* **Purpose:** Secure workspace entry and role verification.
* **Core Components:**
  * PowerCortex lightning bolt branding logo and system title.
  * Sub-header: *"Enter credentials to manage grid intelligence"*.
  * Input Fields: Email Address and Password with validation support.
  * Trigger Buttons: Secure `[Log In]` and a text-based `Forgot Password` link.
* **Authentication Details:** Async JWT validation with backend mapping for role-based system privileges (Operator vs. Administrator).

### [3] Dashboard (Main Command Center)
* **Executive Summary Widget (Top Rack):**
  * Horizontal high-density data panel illustrating today's grid performance:
    * *Current Demand:* `1,420 MW`
    * *Current Supply:* `1,450 MW`
    * *Renewable Contribution:* `34.2%`
    * *Active Faults:* `3` (Critical Badge)
    * *Theft Alerts:* `2` (Warning Badge)
    * *Asset Health Score:* `88%`
* **KPI Metric Cards:**
  * Clean card grids detailing current grid parameters, demand indicators, supply vectors, anomalies, and equipment health rankings.
* **Analytics Charts (Syncfusion Integration):**
  * *Demand Trend:* Interactive Line Chart with actual consumption vs. XGBoost predicted timelines.
  * *Renewable Trend:* Area Chart mapping solar vs. wind energy contributions.
  * *Fault Statistics:* Stacked Bar Chart showcasing active grid issues by priority level.
  * *Theft Analysis:* Pie/Donut Chart mapping billing deviations.
* **AI Insights & Recommendations Module:**
  * Smart system-generated chips tracking high-importance advice:
    * *"Peak demand expected tomorrow at 18:30 (Confidence 94%)."*
    * *"Transformer T-101 risk rating increased by 12%. Scheduled check prompted."*
* **Quick Actions Row:**
  * Quick-access buttons: `[Forecasting Hub]`, `[Asset Monitoring]`, `[Reports & Statistics]`, `[Consult AI Assistant]`.

### [4] Forecasting Page
* **Demand Forecasting Section:**
  * KPI blocks: `Next Hour Forecast`, `Next Day Forecast`, `Next Week Forecast`.
  * *Load Trends Chart:* Line chart comparing historical electricity demand vs. XGBoost model forecasting curves with highlighted confidence margin bands.
  * Output Metrics: `Prediction Confidence %` and `Peak Demand Timing`.
* **Renewable Forecasting Section:**
  * KPI blocks: `Solar Output Forecast`, `Wind Output Forecast`.
  * *Solar Generation Trends:* Area chart depicting projected output based on daylight solar levels.
  * *Wind Generation Trends:* Line chart tracking turbine efficiency relative to wind forecast inputs.
  * Output Metrics: `Renewable Forecast Confidence %`.

### [5] Asset Monitoring Page
* **Core Components:**
  * Category toggle tabs: `[Transformers]`, `[Feeders]`, `[Distribution Assets]`, `[Transmission Assets]`.
  * Search bar to locate specific physical hardware serial tags.
* **Equipment List / Grid Details:**
  * Equipment ID Name (e.g., *"Transformer T-101"*).
  * Radial Health Score progress gauges.
  * ML Risk Scores & Failure Probabilities (%).
  * Telemetry updates: Temperature (°C), Voltage (kV), Current (A), Oil Level (%), Load Capacity (%).
  * Last database telemetry check timestamp.
* **Actions Deck:**
  * Double tap or expandable card sheet reveals **AI Maintenance Suggestions** generated dynamically.

### [6] Fault & Theft Detection Page
Organized into an elegant two-tab utility screen:

* **Tab A: Fault Detection Center**
  * *Incident Feed:* Lists all active electrical anomalies.
  * *Severity Indicators:* High contrast status chips (Critical, High, Medium, Low).
  * *Voltage & Overload Diagnostics:* Metrics outlining active Voltage Sags, Swells, Overload vectors, or physical Line cuts.
  * *Visualizations:* Incident trigger timeline with click-through detail routes.
* **Tab B: Theft Detection Center**
  * *Suspicious Accounts Queue:* Ordered table highlighting account numbers exhibiting anomalous electricity usage patterns.
  * *Consumption Comparative Charts:* Interactive graph detailing predicted normal baseline usage patterns vs. flatlining anomalies.
  * *Theft Probability Rating:* Anomaly scores (%) calculated via background Isolation Forest models.

### [7] AI Assistant Page
* **Core Components:**
  * ChatGPT-style clean bubble chat system.
  * Interactive suggested prompts panel chips.
  * Dynamic prompt input box + secure send button.
* **Example Prompts:**
  * *"Predict tomorrow demand."*
  * *"Show critical transformers."*
  * *"Explain active faults."*
  * *"Generate maintenance recommendations for Substation A."*
* **Capabilities:** RAG-enabled analysis, real-time telemetry lookups, custom report summaries, fault diagnostic explanations.

### [8] Reports & Analytics Page
* **Analytical PDF Engine:**
  * Option filters to compile summaries: *Daily*, *Weekly*, or *Monthly* intervals.
  * Download formats: `[Download PDF]`, `[Download Excel]`.
* **Model Performance Diagnostics:**
  * *Load Forecast Model:* Model accuracy (%), MAE, RMSE, MAPE.
  * *Transformer Health Model:* Model accuracy, Precision, Recall scores.
  * *Fault Detection Model:* Model accuracy, algorithm confidence scores.
  * *Theft Detection Model:* Detection accuracy levels.
* **AI Explainability Section:**
  * Horizontal bar chart illustrating variable feature importances (e.g., Temperature contributing `42%`, Humidity `25%`, Holiday `18%`, Day of Week `15%`).
* **Grid Data Quality Registry:**
  * Active dataset record tallies, last database synchronization timestamps, and verified `Data Quality Scores (%)`.

### [9] System Health Page
* **Ecosystem Diagnostic Panels:**
  * *Backend Server:* FastAPI connectivity status, request counts, response latency (ms).
  * *Database Server:* MongoDB connectivity status, storage disk volume limits (GB).
  * *AI LLM Engine:* Active response codes, prompt routing latency.
  * *ML Pipeline Services:* Diagnostics status check for Forecasting, Fault, and Theft microservices.
* **Connectivity Badges:** Dynamic healthy green (`Online`), amber (`Warning`), or red (`Offline`) indicators.

### [10] Settings Page
* **Core Components:**
  * *Profile Configuration:* View username, employee rank, sub-division ID.
  * *Appearance Controller:* Toggle between Light Mode and Dark Mode.
  * *Notifications Router:* Setup SMS, Email, and Push alarms for active Fault and Theft triggers.
  * *Security Settings:* Secure password modifications, active token managers, and direct logout operations.

---

# 8. Reusable Widgets

### `MetricCard`
* Displays core high-density KPIs.
* *Attributes:* Dynamic system icon, card label title, bold value metric, trend indicator sparkline, and change ratio percentage badge.

### `ForecastCard`
* Houses ML forecast curves. Includes predicted peak thresholds, timing labels, and standard deviations with embedded micro-charts.

### `AssetCard`
* Houses equipment listings. Integrates health status gauges, risk classifications, dynamic state badges, and diagnostic recommendations.

### `AlertCard`
* Severe colored border strip representing severity metrics. Includes incident timestamp, location tags, current readings, and direct isolation control targets.

### `StatusChip`
* Standardized, rounded capsule chip indicating:
  * **Healthy:** Green (`#22C55E`)
  * **Warning:** Amber (`#F59E0B`)
  * **Critical:** Red (`#EF4444`)

### `ChartContainer`
* Unified wrapper for Syncfusion charts offering card layouts, zoom headers, print/export actions, and data filter options.

### `AIMessageBubble`
* Dedicated message bubble segregating user queries from LLM responses, providing full markdown lists, bold metrics, and clickable equipment redirections.

---

# 9. Responsive Layouts

## Mobile
* **Breakpoint:** `0 – 600 px`
* **Layout Design:** Unified single-column stack. Sidebar headers wrap to action toggles.
* **Navigation:** Responsive Bottom Navigation Bar anchored to the bottom.

## Tablet
* **Breakpoint:** `601 – 1024 px`
* **Layout Design:** Two-column grid configurations. Cards arrange side-by-side.
* **Navigation:** Persistent Navigation Rail.

## Desktop
* **Breakpoint:** `1025 px +`
* **Layout Design:** Dense multi-column layouts (Navigation rail + analytics center + alert tracking dashboard).
* **Navigation:** Persistent left-side Navigation Sidebar.

---

# 10. Dark Mode

PowerCortex supports complete dark theme integration across all pages to protect engineers working long operational shifts in dimmed control rooms.

* **Background Theme:** Deep Navy `#0B1220`
* **Cards & Surfaces:** Slate Charcoal `#111827`
* **Text / Primary Elements:** Crisp Off-White `#F8FAFC`
* **Visual contrast:** Cards maintain subtle slate borders and bright status chips (glowing green/amber/red indicators) to secure legibility without causing screen-glare fatigue.

---

# 11. Animation Guidelines

* **Allowed Animations:**
  * Smooth Fade In/Out for page routes.
  * Scale and Expand micro-motions when loading charts.
  * Sliding drawer transitions for sidebar drawers.
* **Motion Constraints:**
  * Bouncing curves, high-velocity particle animations, and distracting effects are strictly avoided.
  * Transitions are optimized to execute within **200ms - 300ms** to ensure a premium industrial utility platform feel.

---

# 12. UI Development Stack

* **Frontend Framework:** `Flutter` (Stable Channel) & `Dart`
* **State Management:** `GetX`
* **Visual Library:** `Material 3`
* **API Integration Layer:** `Dio` (HTTP Client)
* **Data Visualization:** `Syncfusion Flutter Charts`
* **Backend Framework:** `FastAPI` (Python)
* **Database Driver:** `MongoDB` (Motor Driver)
* **Machine Learning Modules:** `XGBoost`, `Random Forest`, `Isolation Forest`, `TensorFlow`
* **AI Conversational Assistant:** `Qwen 3`, `OpenRouter API`, `Groq API`, `NVIDIA API`
* **Infrastructure Deployment:** `Docker`, `Docker Compose`, `Nginx`

---

# 13. Final Goal

PowerCortex delivers a production-grade utility operations platform that blends rich enterprise analytical grids, machine learning time-series forecasting, automated fault/theft anomaly detection, and natural language AI insights. It is structured into an optimized, highly robust 10-page layout that is both visually spectacular and highly maintainable for modern utility organizations.
