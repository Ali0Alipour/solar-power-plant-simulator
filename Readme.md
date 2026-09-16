# ☀️ Solar Power Plant Simulator

#### Video Demo: <URL HERE>

#### Description:

Solar Power Plant Simulator is a comprehensive Python-based tool that simulates the performance, economics, and optimization of photovoltaic (PV) solar power plants at any location worldwide. This project combines real-time meteorological data, particle swarm optimization (PSO), and financial analysis to help users design and evaluate solar installations.

## 🎯 Project Overview

This simulator was developed as a final project for CS50's Introduction to Programming with Python (CS50P). It addresses a real-world engineering problem: **how to determine the optimal solar panel configuration for a given location considering both technical performance and economic viability**.

The tool is particularly relevant to my field of study (Electrical Power Engineering) and bridges programming skills with renewable energy domain expertise.

## ✨ Key Features

### 1. Global Location Support
- Accepts any city name worldwide (e.g., "Tehran", "Paris", "Kerman")
- Automatically converts city names to geographic coordinates using the Nominatim API
- Detects the country automatically using reverse geocoding
- Supports 9+ countries with specific electricity feed-in tariff (FIT) rates

### 2. Real-Time Solar Data
- Fetches actual solar radiation data from **NASA POWER API**
- Retrieves daily irradiance values (kWh/m²/day) for an entire year
- Uses real historical data (2024) for accurate simulation

### 3. PSO Optimization
- Implements a **Particle Swarm Optimization** algorithm to find the best solar panel
- Optimizes two decision variables: panel power (300W - 600W) and panel technology (Monocrystalline, Polycrystalline, Thin Film, Bifacial)
- Fitness function minimizes cost per kWh while maximizing efficiency

### 4. Comprehensive Economic Analysis
- **On-Grid vs Off-Grid comparison**
- Equipment costs (panels, inverters, cables, installation, etc.)
- Country-specific feed-in tariffs (FIT)
- Real-time currency exchange rates
- Payback period calculation
- Return on Investment (ROI)

### 5. Sensitivity Analysis
- Tests system performance under ±20% radiation changes
- Shows how energy production and revenue scale with solar conditions
- Helps understand investment risk

### 6. PDF Report Generation
- Professional 3-page PDF report
- System information table
- Balance of System (BOS) table
- Monthly and daily energy production charts
- CO2 savings calculation

### 7. Interactive Menu System
- 7-option interactive menu
- Save/load/compare simulations
- Delete/rename saved simulations
- Compare multiple scenarios side-by-side

## 📁 File Structure

### project.py

The main application file containing all core functions:

- **main()**: Entry point that displays the interactive menu and handles user choices
- **get_coordinates(city_name)**: Converts city name to latitude/longitude using OpenStreetMap's Nominatim API
- **get_country_from_coordinates(lat, lon)**: Detects country code from coordinates using reverse_geocoder
- **fetch_solar_data(lat, lon)**: Retrieves solar radiation data from NASA POWER API for the entire year 2024
- **calculate_energy(radiation, total_power, panel_power, panel_area, efficiency)**: Calculates annual energy production
- **calculate_cost(total_power, grid_type)**: Computes total system cost based on equipment prices and grid type
- **get_fit_rate(country_code, total_power)**: Returns the appropriate FIT rate for the country and power range
- **calculate_revenue(total_energy, total_power, country_code)**: Calculates annual revenue in local currency and USD
- **calculate_payback(total_cost, annual_revenue)**: Calculates payback period in years
- **pso_optimize(lat, lon, total_power, grid_type, radiation_data)**: Runs the PSO algorithm to find the optimal panel
- **compare_scenarios(lat, lon, radiation, total_power, country_code)**: Compares On-Grid and Off-Grid scenarios
- **sensitivity_analysis(radiation_data, total_power, country_code)**: Analyzes system behavior under varying radiation conditions
- **generate_pdf_report(...)**: Creates a professional PDF report with charts and tables
- **save_last_simulation(last_result)**: Saves the current simulation with a custom name
- **load_saved_simulation()**: Loads and displays a previously saved simulation
- **compare_saved_simulations()**: Compares multiple saved simulations side-by-side
- **delete_saved_simulation()**: Deletes a saved simulation (JSON + PDF)
- **rename_saved_simulation()**: Renames a saved simulation file
- **show_banner(), show_menu(), run_simulation()**: UI helper functions

### test_project.py

Contains **51 unit tests** using pytest, covering:

- **API tests**: Verify coordinate lookup, country detection, solar data fetching, exchange rate retrieval
- **Calculation tests**: Energy, cost, revenue, payback calculations
- **PSO tests**: Verify the optimizer returns valid results
- **Data structure tests**: Verify integrity of panel database, equipment prices, FIT rates
- **File management tests**: Test save/load/delete/rename functionality
- **Edge cases**: Zero radiation, zero power, invalid countries
- **Integration tests**: Full flow from input to output

### requirements.txt and request.txt

Lists all pip-installable dependencies:

- requests: HTTP requests for APIs
- reverse_geocoder: Offline country detection from coordinates
- matplotlib: Chart generation
- pandas: Data manipulation
- fpdf2: PDF generation
- pillow: Image processing
- pytest: Testing framework

### saved_simulations/ (auto-created)

Stores saved simulations as JSON (data) and PDF (report) files.

## 🧠 Design Decisions

### Why PSO?

I chose Particle Swarm Optimization because:

1. It's a proven metaheuristic algorithm that I've used in my thesis work (capacitor placement optimization)
2. It handles discrete variables well (technology choice) combined with continuous ones (power)
3. It converges quickly for this 2-dimensional problem
4. It doesn't require gradient information

### Why NASA POWER?

After testing multiple APIs (PVGIS, SolarGIS, OpenWeather), NASA POWER was selected because:

- It's completely free with no authentication required
- Provides daily irradiance data at 1°×1° resolution
- Reliable and well-documented
- Long historical data available

### Why Multi-Country Support?

Since solar investment is a global concern, the tool needed to work worldwide. I included 9 countries with their specific FIT rates, and the currency conversion uses real-time exchange rates from CurrencyAPI.

### Why On-Grid vs Off-Grid?

This is a fundamental decision in solar plant design. On-Grid is cheaper but requires grid connection; Off-Grid needs batteries (expensive) but works in remote areas. Comparing both helps users make informed decisions.

### Why PDF Reports?

The PDF output mimics professional PVsyst reports used by solar engineers, including:

- System information
- Balance of System (BOS) table
- Performance Ratio (PR)
- Normalized Production (kWh/kWp)
- Monthly and daily production charts
- CO2 avoided

## 📊 Sample Output

For a 20 kW plant in Paris:

```
📊 SOLAR PLANT SIMULATION RESULTS
📍 Location: paris
🌍 Country: France
📅 Days with data: 366 days
☀️ Average Daily Radiation: 3.09 kWh/m²/day
📦 Panel Type: Thin Film 300W
📦 Number of Panels: 67 panels
🔋 Annual Energy Production: 31,623 kWh/year

💰 ECONOMIC ANALYSIS
💵 Total Cost (USD): $17,950
💶 Annual Revenue: €4,111 ($3,535)
📈 Payback Period: 5.1 years
📊 ROI: 19.7% per year
```

## 🚀 How to Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the simulator:

```bash
python project.py
```

3. Run tests:

```bash
pytest test_project.py -v
```

## ⚠️ Important Notes

- **Internet connection required** for API calls (NASA POWER, Nominatim, CurrencyAPI)
- The first run may take 30-60 seconds due to API calls
- Solar data is for year 2024 (real historical data)
- Currency rates are fetched in real-time
- All calculations are estimates and should be validated by professional engineers before real investment

## 🔮 Future Improvements

- Add ML-based degradation modeling over 25 years
- Include shading analysis using solar position algorithms
- Support more countries and FIT rates
- Add Streamlit web dashboard
- Include battery sizing optimization for Off-Grid systems

## 🙏 Acknowledgments

- NASA POWER for providing free solar radiation data
- OpenStreetMap/Nominatim for free geocoding
- CurrencyAPI for real-time exchange rates
- CS50 team for the excellent course structure
- My thesis advisor for inspiring the PSO application

## 📜 License

This project was created as part of CS50's Introduction to Programming with Python course.

---

**Author**: Ali Alipour
**Course**: CS50P - Introduction to Programming with Python
**Year**: 2026
