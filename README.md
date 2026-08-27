# 🏎️ F1 Pit Wall Strategy Dashboard

An interactive, live-data Formula 1 strategy and telemetry analysis application built with Python and Streamlit. 

This application transforms raw gigabytes of FIA timing, weather, and GPS data into a professional-grade "Pit Wall" dashboard. It allows users to act as a race engineer by analyzing tire degradation, live tactical pit windows, and micro-sector driver telemetry in real-time.

---

## 🚀 Project Overview

Modern Formula 1 is driven by data. This project replicates the proprietary software used by F1 strategists on the pit wall. By connecting to the Ergast API and FIA Live Timing data (via FastF1), this dashboard processes millions of data points to provide actionable insights into race pace, strategic crossovers, and telemetry traces.

## ✨ Key Features & Modules

The application is divided into a modular 12-part system, covering every aspect of race strategy:

1. **Tire Degradation Monitor:** Rolling-average pace smoothing and outlier filtering to track true tire drop-off over a stint.
2. **Official Classification:** Live and historical race results with F1 broadcast-style UI components.
3. **Undercut Radar:** Projects pit-stop deltas to determine if a trailing car can successfully "undercut" the car ahead.
4. **Catch-Up Projection:** Calculates the exact lap a chasing car will overtake a defending car based on pace deltas.
5. **Micro-Sector Battles:** Analyzes mini-sector dominance between two drivers across a single lap.
6. **DRS Train Radar:** Identifies field compression and DRS dependency clusters.
7. **Crossover Point Alert:** Determines the optimal lap to switch between Wet/Intermediate/Slick tires based on track evolution.
8. **Monte Carlo Oracle:** Probabilistic race simulations using historical pace data.
9. **Season Evolution:** Interactive trajectory tracking of the Drivers' Championship across the season.
10. **Strategy Optimizer:** Calculates the fastest theoretical pit-stop strategy for a given race.
11. **Telemetry Overlays:** High-resolution GPS track mapping using $X_{new} = X \cos(\theta) - Y \sin(\theta)$ rotation matrices to visualize throttle, braking, and gear traces across any lap.
12. **Flash Tactical Alert Engine:** A live decision matrix that calculates the mathematical viability of pitting under a Virtual Safety Car (VSC), Safety Car (SC), or Red Flag based on track position and tire degradation models.

---

## 🛠️ Technology Stack

* **Language:** Python 3
* **Frontend Framework:** Streamlit
* **Data Engineering:** FastF1, Pandas, NumPy
* **Data Visualization:** Plotly (Express & Graph Objects)
* **Caching & Performance:** Streamlit `@cache_data`, SQLite HTTP caching

---

## 🏗️ Project Architecture

The application follows a strict Modular MVC (Model-View-Controller) architecture to ensure scalability and clean code:

```text
F1_PitWall/
│
├── app.py                      # Master routing engine and UI sidebar configuration
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git rules to prevent uploading heavy cache files
│
├── modules/                    # Independent logic for all 12 analytical tools
│   ├── mod1_tire_deg.py
│   ├── mod2_classification.py
│   ├── ...
│   └── mod12_tactical_alert.py
│
├── utils/                      # Data engineering and processing layer
    └── data_loader.py          # FastF1 caching logic and universal helper functions

---

## 💻 Installation & Setup

To run this application on your local machine:

**1. Clone the repository:**
```bash
git clone [https://github.com/ritapardo/f1-pitwall-dashboard](https://github.com/ritapardo/f1-pitwall-dashboard.git)

**2. Install dependencies:**
pip install -r requirements.txt

**3. Launch the application:**
python -m streamlit run app.py  

or 

streamlit run app.py

### ⚠️ A Note on Data Caching & API Limits
This application pulls massive amounts of data from the `api.jolpi.ca` (Ergast mirror) and the FIA live timing servers. 

* **Initial Load:** The first time you select a new session, it may take 30–60 seconds to download the telemetry.
* **Smart Caching:** The app uses local caching. Once a race is loaded once, subsequent loads are instantaneous. If the external API times out, the app is engineered to gracefully fall back to the cached SQLite database.
