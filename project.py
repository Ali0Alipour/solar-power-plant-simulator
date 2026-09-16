import requests
import json
from datetime import datetime, timedelta
import reverse_geocoder as rg
import random
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from fpdf import FPDF
import io
import os
import time
from PIL import Image
import tempfile
import shutil

CURRENCY_API_KEY = "Put your API key here"

PANEL_DATABASE = {
    "mono_400": {"name": "Monocrystalline 400W", "power": 0.4, "area": 2.0, "efficiency": 0.20, "price_per_watt": 0.35, "price_per_panel": 140, "image": "🔵"},
    "mono_550": {"name": "Monocrystalline 550W", "power": 0.55, "area": 2.5, "efficiency": 0.21, "price_per_watt": 0.32, "price_per_panel": 176, "image": "🔵"},
    "poly_450": {"name": "Polycrystalline 450W", "power": 0.45, "area": 2.2, "efficiency": 0.18, "price_per_watt": 0.28, "price_per_panel": 126, "image": "🟣"},
    "thin_300": {"name": "Thin Film 300W", "power": 0.3, "area": 3.0, "efficiency": 0.15, "price_per_watt": 0.25, "price_per_panel": 75, "image": "🟢"},
    "bifacial_500": {"name": "Bifacial 500W", "power": 0.5, "area": 2.4, "efficiency": 0.22, "price_per_watt": 0.40, "price_per_panel": 200, "image": "✨"}
}

EQUIPMENT_PRICES = {
    "panel": 320, "inverter": 150, "structure": 70, "cables": 40,
    "switchgear": 60, "installation": 120, "permits": 30, "transport": 25, "battery": 400
}

FIT_RATES = {
    "IR": {"currency": "IRR", "symbol": "تومان", "name": "Iran", "rates": [
        {"max_power": 10, "rate": 5000}, {"max_power": 100, "rate": 4500}, {"max_power": 500, "rate": 4000}]},
    "FR": {"currency": "EUR", "symbol": "€", "name": "France", "rates": [
        {"max_power": 3, "rate": 0.103}, {"max_power": 9, "rate": 0.088}, {"max_power": 36, "rate": 0.130}, {"max_power": 100, "rate": 0.113}, {"max_power": 500, "rate": 0.105}]},
    "DE": {"currency": "EUR", "symbol": "€", "name": "Germany", "rates": [
        {"max_power": 10, "rate": 0.082}, {"max_power": 40, "rate": 0.075}, {"max_power": 100, "rate": 0.068}, {"max_power": 500, "rate": 0.060}]},
    "US": {"currency": "USD", "symbol": "$", "name": "United States", "rates": [
        {"max_power": 10, "rate": 0.12}, {"max_power": 100, "rate": 0.10}, {"max_power": 500, "rate": 0.08}]},
    "GB": {"currency": "GBP", "symbol": "£", "name": "United Kingdom", "rates": [
        {"max_power": 10, "rate": 0.15}, {"max_power": 100, "rate": 0.12}, {"max_power": 500, "rate": 0.10}]},
    "CA": {"currency": "CAD", "symbol": "$", "name": "Canada", "rates": [
        {"max_power": 10, "rate": 0.10}, {"max_power": 100, "rate": 0.08}, {"max_power": 500, "rate": 0.06}]},
    "IT": {"currency": "EUR", "symbol": "€", "name": "Italy", "rates": [
        {"max_power": 3, "rate": 0.095}, {"max_power": 20, "rate": 0.085}, {"max_power": 100, "rate": 0.075}, {"max_power": 500, "rate": 0.065}]},
    "ES": {"currency": "EUR", "symbol": "€", "name": "Spain", "rates": [
        {"max_power": 10, "rate": 0.090}, {"max_power": 100, "rate": 0.080}, {"max_power": 500, "rate": 0.070}]},
    "AU": {"currency": "AUD", "symbol": "$", "name": "Australia", "rates": [
        {"max_power": 10, "rate": 0.08}, {"max_power": 100, "rate": 0.06}, {"max_power": 500, "rate": 0.05}]}
}

COUNTRY_CURRENCY = {
    "IR": {"currency": "IRR", "symbol": "تومان"},
    "FR": {"currency": "EUR", "symbol": "€"},
    "DE": {"currency": "EUR", "symbol": "€"},
    "US": {"currency": "USD", "symbol": "$"},
    "GB": {"currency": "GBP", "symbol": "£"},
    "CA": {"currency": "CAD", "symbol": "$"},
    "IT": {"currency": "EUR", "symbol": "€"},
    "ES": {"currency": "EUR", "symbol": "€"},
    "AU": {"currency": "AUD", "symbol": "$"}
}

TECHNOLOGIES = {
    "mono": {"name": "Monocrystalline", "efficiency_range": (0.18, 0.22), "price_range": (0.30, 0.40), "degradation": 0.005},
    "poly": {"name": "Polycrystalline", "efficiency_range": (0.15, 0.18), "price_range": (0.25, 0.32), "degradation": 0.008},
    "thin": {"name": "Thin Film", "efficiency_range": (0.12, 0.16), "price_range": (0.20, 0.28), "degradation": 0.010},
    "bifacial": {"name": "Bifacial", "efficiency_range": (0.20, 0.24), "price_range": (0.38, 0.48), "degradation": 0.004}
}

SAVED_DIR = "saved_simulations"
os.makedirs(SAVED_DIR, exist_ok=True)


def get_irr_exchange_rate():
    try:
        url = "https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=irr"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data["stats"]["usdt-irr"]["bestSell"]) / 10
    except:
        pass
    try:
        url = "https://api.priceto.day/v1/latest/irr/usd"
        response = requests.get(url, timeout=10)
        return response.json()["usd"]
    except:
        pass
    try:
        url = "https://api.currencyapi.com/v3/latest"
        params = {"apikey": CURRENCY_API_KEY, "base_currency": "USD", "currencies": "IRR"}
        response = requests.get(url, params=params, timeout=10)
        return response.json()["data"]["IRR"]["value"] / 10
    except:
        pass
    return 220000


def get_exchange_rate(from_currency, to_currency="USD"):
    try:
        url = "https://api.currencyapi.com/v3/latest"
        params = {"apikey": CURRENCY_API_KEY, "base_currency": from_currency, "currencies": to_currency}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if "data" in data and to_currency in data["data"]:
            return data["data"][to_currency]["value"]
        return None
    except:
        return None


def get_coordinates(city_name):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": city_name, "format": "json", "limit": 1}
        headers = {"User-Agent": "SolarSimulator/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None, None
    except:
        return None, None


def get_country_from_coordinates(lat, lon):
    try:
        result = rg.search((lat, lon))
        if result:
            return result[0]['cc'], result[0]['name']
        return None, None
    except:
        return None, None


def fetch_solar_data(lat, lon):
    try:
        url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        params = {
            "parameters": "ALLSKY_SFC_SW_DWN", "community": "RE",
            "longitude": lon, "latitude": lat,
            "start": "20240101", "end": "20241231", "format": "JSON"
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    except:
        return None


def calculate_energy(radiation, total_power, panel_power, panel_area, efficiency):
    panel_count = total_power / panel_power
    total_energy = 0
    for date, rad in radiation.items():
        total_energy += rad * panel_area * panel_count * efficiency
    return total_energy, panel_count


def calculate_cost(total_power, grid_type):
    cost = 0.0
    for item, price_per_kw in EQUIPMENT_PRICES.items():
        if item == "battery" and grid_type == "on-grid":
            continue
        cost += price_per_kw * total_power
    return cost


def get_fit_rate(country_code, total_power):
    if country_code not in FIT_RATES:
        return None, None, None, None
    country_data = FIT_RATES[country_code]
    for rate_entry in country_data["rates"]:
        if total_power <= rate_entry["max_power"]:
            return rate_entry["rate"], country_data["currency"], country_data["symbol"], country_data["name"]
    return country_data["rates"][-1]["rate"], country_data["currency"], country_data["symbol"], country_data["name"]


def get_local_currency(country_code):
    if country_code in COUNTRY_CURRENCY:
        return COUNTRY_CURRENCY[country_code]["currency"], COUNTRY_CURRENCY[country_code]["symbol"]
    return None, None


def calculate_revenue(total_energy, total_power, country_code):
    fit_rate, currency, symbol, country_name = get_fit_rate(country_code, total_power)
    if fit_rate is None:
        return None, None, None, None
    annual_revenue_local = total_energy * fit_rate
    if currency != "USD":
        exchange_rate = get_exchange_rate(currency, "USD")
        annual_revenue_usd = annual_revenue_local / exchange_rate if exchange_rate else None
    else:
        annual_revenue_usd = annual_revenue_local
    return annual_revenue_local, annual_revenue_usd, symbol, country_name


def calculate_payback(total_cost, annual_revenue):
    if annual_revenue and annual_revenue > 0:
        return total_cost / annual_revenue
    return None


def pso_optimize(lat, lon, total_power, grid_type, radiation_data):
    NUM_PARTICLES = 30
    MAX_ITERATIONS = 50
    W, C1, C2 = 0.7, 1.5, 1.5
    POWER_MIN, POWER_MAX = 0.3, 0.6
    TECH_LIST = list(TECHNOLOGIES.keys())

    def calculate_panel_performance(tech, power):
        tech_info = TECHNOLOGIES[tech]
        efficiency = random.uniform(tech_info["efficiency_range"][0], tech_info["efficiency_range"][1])
        price_per_watt = random.uniform(tech_info["price_range"][0], tech_info["price_range"][1])
        panel_price = power * 1000 * price_per_watt
        panel_count = total_power / power
        panel_area = 2.0 + (power - 0.3) * 2.5

        total_energy = 0
        for date, rad in radiation_data.items():
            total_energy += rad * panel_area * panel_count * efficiency

        panel_cost = panel_price * panel_count
        total_cost = panel_cost
        for item, price in EQUIPMENT_PRICES.items():
            if item == "battery" and grid_type == "on-grid":
                continue
            if item != "panel":
                total_cost += price * total_power

        cost_per_kwh = total_cost / total_energy if total_energy > 0 else float('inf')

        return {
            "total_energy": total_energy, "total_cost": total_cost,
            "panel_count": panel_count, "efficiency": efficiency,
            "cost_per_kwh": cost_per_kwh
        }

    def fitness_function(tech, power):
        result = calculate_panel_performance(tech, power)
        penalty = 1.0
        if result["cost_per_kwh"] > 0.5:
            penalty += (result["cost_per_kwh"] - 0.5) * 10
        if result["efficiency"] < 0.15:
            penalty += (0.15 - result["efficiency"]) * 100
        return result["cost_per_kwh"] * penalty, result

    particles, velocities, personal_best_pos, personal_best_fitness = [], [], [], []

    for i in range(NUM_PARTICLES):
        tech_idx = random.randint(0, len(TECH_LIST) - 1)
        power = random.uniform(POWER_MIN, POWER_MAX)
        particles.append([tech_idx, power])
        velocities.append([random.uniform(-0.5, 0.5), random.uniform(-0.05, 0.05)])
        tech = TECH_LIST[tech_idx]
        fitness, _ = fitness_function(tech, power)
        personal_best_pos.append([tech_idx, power])
        personal_best_fitness.append(fitness)

    global_best_idx = personal_best_fitness.index(min(personal_best_fitness))
    global_best_pos = personal_best_pos[global_best_idx].copy()
    global_best_fitness = personal_best_fitness[global_best_idx]

    print("\n🧠 Running PSO optimization...")

    for iteration in range(MAX_ITERATIONS):
        for i in range(NUM_PARTICLES):
            r1, r2 = random.random(), random.random()
            velocities[i][0] = (W * velocities[i][0] +
                               C1 * r1 * (personal_best_pos[i][0] - particles[i][0]) +
                               C2 * r2 * (global_best_pos[0] - particles[i][0]))
            velocities[i][1] = (W * velocities[i][1] +
                               C1 * r1 * (personal_best_pos[i][1] - particles[i][1]) +
                               C2 * r2 * (global_best_pos[1] - particles[i][1]))
            velocities[i][0] = max(-1, min(1, velocities[i][0]))
            velocities[i][1] = max(-0.1, min(0.1, velocities[i][1]))
            particles[i][0] = int(round(particles[i][0] + velocities[i][0]))
            particles[i][1] = particles[i][1] + velocities[i][1]
            particles[i][0] = max(0, min(len(TECH_LIST) - 1, particles[i][0]))
            particles[i][1] = max(POWER_MIN, min(POWER_MAX, particles[i][1]))
            tech = TECH_LIST[particles[i][0]]
            fitness, _ = fitness_function(tech, particles[i][1])
            if fitness < personal_best_fitness[i]:
                personal_best_fitness[i] = fitness
                personal_best_pos[i] = particles[i].copy()
            if fitness < global_best_fitness:
                global_best_fitness = fitness
                global_best_pos = particles[i].copy()
        if iteration % 10 == 0:
            print(f"  Iteration {iteration}: Best fitness = {global_best_fitness:.4f}")

    best_tech = TECH_LIST[global_best_pos[0]]
    best_power = global_best_pos[1]
    best_fitness, best_result = fitness_function(best_tech, best_power)

    best_panel_key = None
    for key, panel in PANEL_DATABASE.items():
        if abs(panel["power"] - best_power) < 0.05:
            best_panel_key = key
            break
    if best_panel_key is None:
        best_panel_key = "mono_550"

    result = {
        "best_panel_key": best_panel_key,
        "best_panel": PANEL_DATABASE[best_panel_key],
        "best_tech": best_tech, "best_power": best_power,
        "best_fitness": best_fitness,
        "best_energy": best_result["total_energy"],
        "best_cost": best_result["total_cost"],
        "best_efficiency": best_result["efficiency"],
        "best_panel_count": best_result["panel_count"],
        "best_cost_per_kwh": best_result["cost_per_kwh"]
    }

    print(f"\n✅ PSO optimization complete!")
    print(f"   Best panel: {result['best_panel']['name']}")
    print(f"   Best power: {best_power*1000:.0f}W")
    print(f"   Cost per kWh: ${result['best_cost_per_kwh']:.4f}")

    return result


def generate_pdf_report(radiation_data, total_energy, total_power, panel_count,
                        panel_efficiency, total_cost, annual_revenue, payback_years,
                        country_name, location, grid_type, panel_name, lat, lon, country_code,
                        custom_name=None):
    try:
        dates, rad_values = [], []
        for date_str, rad in radiation_data.items():
            dates.append(datetime.strptime(date_str, "%Y%m%d"))
            rad_values.append(rad)

        panel_area = 2.5
        efficiency = panel_efficiency / 100
        daily_energy = [rad * panel_area * panel_count * efficiency for rad in rad_values]

        df = pd.DataFrame({'date': dates, 'radiation': rad_values, 'energy': daily_energy})
        df['month'] = df['date'].dt.month
        monthly_energy = df.groupby('month')['energy'].sum()

        normalized_production = total_energy / total_power
        theoretical_energy = total_energy / 0.85
        performance_ratio = (total_energy / theoretical_energy) * 100 if theoretical_energy > 0 else 0

        class PDF(FPDF):
            def header(self):
                self.set_font('helvetica', 'B', 16)
                self.cell(0, 10, 'SOLAR PLANT SIMULATION REPORT', 0, 1, 'C')
                self.ln(5)
            def footer(self):
                self.set_y(-15)
                self.set_font('helvetica', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

        pdf = PDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()

        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 8, '1. SYSTEM INFORMATION', 0, 1, 'L')
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(3)

        pdf.set_font('helvetica', '', 10)
        info_data = [
            ['Location', location], ['Country', country_name],
            ['Latitude', f'{lat:.4f}°'], ['Longitude', f'{lon:.4f}°'],
            ['Total Power', f'{total_power:.1f} kWp'], ['Panel Type', panel_name],
            ['Number of Panels', f'{panel_count:.0f}'], ['Panel Efficiency', f'{panel_efficiency:.1f}%'],
            ['Grid Type', grid_type],
        ]
        for label, value in info_data:
            pdf.cell(60, 7, f'{label}:', 0, 0, 'R')
            pdf.cell(80, 7, f'{value}', 0, 1, 'L')

        pdf.ln(5)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 8, '2. BALANCE AND MAIN RESULTS', 0, 1, 'L')
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(3)

        col_widths = [100, 80, 80]
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(col_widths[0], 8, 'Parameter', 1, 0, 'C')
        pdf.cell(col_widths[1], 8, 'Value', 1, 0, 'C')
        pdf.cell(col_widths[2], 8, 'Unit', 1, 1, 'C')

        pdf.set_font('helvetica', '', 9)
        balance_data = [
            ['Total Installed Power', f'{total_power:.1f}', 'kWp'],
            ['Annual Energy Production', f'{total_energy:,.0f}', 'kWh/year'],
            ['Normalized Production', f'{normalized_production:.1f}', 'kWh/kWp'],
            ['Performance Ratio (PR)', f'{performance_ratio:.1f}', '%'],
            ['Average Daily Radiation', f'{sum(radiation_data.values()) / len(radiation_data):.2f}', 'kWh/m²/day'],
            ['Total Cost', f'${total_cost:,.2f}', 'USD'],
            ['Annual Revenue', f'${annual_revenue:,.2f}', 'USD/year'],
            ['Payback Period', f'{payback_years:.1f}', 'years'],
            ['CO2 Avoided', f'{total_energy * 0.6 / 1000:.1f}', 'tons/year'],
        ]
        for row in balance_data:
            pdf.cell(col_widths[0], 7, row[0], 1, 0, 'L')
            pdf.cell(col_widths[1], 7, row[1], 1, 0, 'C')
            pdf.cell(col_widths[2], 7, row[2], 1, 1, 'C')

        fig1, ax1 = plt.subplots(figsize=(10, 5))
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        month_values = [monthly_energy.get(m, 0) for m in range(1, 13)]
        ax1.bar(months, month_values, color='orange', alpha=0.7)
        ax1.set_xlabel('Month'); ax1.set_ylabel('Energy (kWh)')
        ax1.set_title(f'Monthly Energy Production - {location}')
        ax1.grid(True, alpha=0.3); plt.tight_layout()
        buf1 = io.BytesIO(); plt.savefig(buf1, format='png', dpi=150); buf1.seek(0); plt.close(fig1)

        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.plot(dates, daily_energy, color='green', linewidth=1, alpha=0.7)
        ax2.set_xlabel('Date'); ax2.set_ylabel('Daily Energy (kWh)')
        ax2.set_title(f'Daily Energy Production - {location}')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45); plt.tight_layout()
        buf2 = io.BytesIO(); plt.savefig(buf2, format='png', dpi=150); buf2.seek(0); plt.close(fig2)

        pdf.add_page()
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 8, '3. CHARTS', 0, 1, 'L')
        pdf.line(10, pdf.get_y(), 280, pdf.get_y())
        pdf.ln(5)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp1:
            tmp1.write(buf1.getvalue()); tmp1_path = tmp1.name
        pdf.image(tmp1_path, x=10, y=pdf.get_y(), w=180); pdf.ln(60)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp2:
            tmp2.write(buf2.getvalue()); tmp2_path = tmp2.name
        pdf.image(tmp2_path, x=10, y=pdf.get_y(), w=180)

        os.unlink(tmp1_path); os.unlink(tmp2_path)

        if custom_name:
            pdf_filename = os.path.join(SAVED_DIR, f"{custom_name}.pdf")
        else:
            pdf_filename = f"solar_report_{location.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        pdf.output(pdf_filename)
        return pdf_filename

    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        return None


def compare_scenarios(lat, lon, radiation, total_power, country_code):
    scenarios = {}
    for grid_type in ["on-grid", "off-grid"]:
        print(f"\n📊 Analyzing {grid_type.upper()} scenario...")
        pso_result = pso_optimize(lat, lon, total_power, grid_type, radiation)
        _, annual_revenue_usd, _, _ = calculate_revenue(pso_result["best_energy"], total_power, country_code)
        payback = calculate_payback(pso_result["best_cost"], annual_revenue_usd)
        scenarios[grid_type] = {
            "panel": pso_result["best_panel"]["name"],
            "energy": pso_result["best_energy"],
            "cost": pso_result["best_cost"],
            "revenue": annual_revenue_usd,
            "payback": payback,
            "roi": (1/payback * 100) if payback else 0
        }
    return scenarios


def sensitivity_analysis(radiation_data, total_power, country_code):
    results = []
    for factor in [0.8, 0.9, 1.0, 1.1, 1.2]:
        modified = {date: rad * factor for date, rad in radiation_data.items()}
        total_energy, _ = calculate_energy(modified, total_power, 0.55, 2.5, 0.18)
        _, annual_revenue_usd, _, _ = calculate_revenue(total_energy, total_power, country_code)
        results.append({"radiation_factor": factor, "energy": total_energy, "revenue": annual_revenue_usd})
    return results


def show_banner():
    print("\n" + "=" * 65)
    print("☀️  SOLAR POWER PLANT SIMULATOR  ☀️".center(65))
    print("=" * 65)


def show_menu():
    print("\n" + "=" * 65)
    print("📋 MAIN MENU".center(65))
    print("=" * 65)
    print("  1. 🚀  Run New Simulation")
    print("  2. 💾  Save Last Simulation (Custom Name)")
    print("  3. 📂  Load & View Saved Simulation")
    print("  4. 📊  Compare Saved Simulations")
    print("  5. 🗑️   Delete Saved Simulation")
    print("  6. ✏️   Rename Saved Simulation")
    print("  7. ❌  Exit")
    print("=" * 65)


def run_simulation():
    print("\n" + "=" * 60)
    print("🚀 NEW SIMULATION")
    print("=" * 60)

    location = input("Enter city name (e.g., Tehran): ").strip()
    if not location:
        print("❌ Location cannot be empty!")
        return None

    try:
        total_power = float(input("Enter total plant capacity (kW): "))
        if total_power <= 0:
            print("❌ Capacity must be positive!")
            return None
    except ValueError:
        print("❌ Invalid number!")
        return None

    grid_type = input("Enter grid type (on-grid/off-grid): ").strip().lower()
    while grid_type not in ["on-grid", "off-grid"]:
        print("❌ Invalid input! Please enter 'on-grid' or 'off-grid'")
        grid_type = input("Enter grid type (on-grid/off-grid): ").strip().lower()

    print(f"\n📍 Finding coordinates for {location}...")
    lat, lon = get_coordinates(location)
    if lat is None:
        print("❌ Could not find location!")
        return None
    print(f"✅ Latitude: {lat:.4f}, Longitude: {lon:.4f}")

    print("🗺️ Detecting country from coordinates...")
    country_code, country_name = get_country_from_coordinates(lat, lon)
    if country_code is None:
        print("⚠️ Could not detect country.")
        country_code = input("Enter country code (IR, FR, DE, US, GB, CA, IT, ES, AU): ").strip().upper()
        country_name = country_code
    else:
        print(f"✅ Country detected: {country_name} ({country_code})")

    print("\n📡 Fetching solar radiation data from NASA POWER...")
    radiation = fetch_solar_data(lat, lon)
    if radiation is None:
        print("❌ Failed to fetch solar data!")
        return None

    avg_radiation = sum(radiation.values()) / len(radiation)

    print("\n🧠 Starting PSO optimization...")
    pso_result = pso_optimize(lat, lon, total_power, grid_type, radiation)

    best_panel = pso_result["best_panel"]
    best_energy = pso_result["best_energy"]
    best_cost = pso_result["best_cost"]
    best_panel_count = pso_result["best_panel_count"]
    best_efficiency = pso_result["best_efficiency"]

    print("\n💰 Calculating economics...")

    total_cost_local, total_cost_local_symbol = None, None
    if country_code == "IR":
        exchange_rate_toman = get_irr_exchange_rate()
        if exchange_rate_toman:
            total_cost_local = best_cost * exchange_rate_toman
            total_cost_local_symbol = "تومان"
    else:
        local_currency, local_symbol = get_local_currency(country_code)
        if local_currency and local_currency != "USD":
            exchange_rate = get_exchange_rate("USD", local_currency)
            if exchange_rate:
                total_cost_local = best_cost * exchange_rate
                total_cost_local_symbol = local_symbol

    annual_revenue_local, annual_revenue_usd, currency_symbol, country_name = calculate_revenue(
        best_energy, total_power, country_code
    )
    payback_years = calculate_payback(best_cost, annual_revenue_usd)

    print("\n" + "=" * 60)
    print("📊 SOLAR PLANT SIMULATION RESULTS")
    print("=" * 60)
    print(f"📍 Location: {location}")
    print(f"🌍 Country: {country_name or country_code}")
    print(f"🌍 Latitude: {lat:.4f}, Longitude: {lon:.4f}")
    print(f"📅 Days with data: {len(radiation)} days")
    print(f"☀️ Average Daily Radiation: {avg_radiation:.2f} kWh/m²/day")
    print(f"☀️ Total Annual Radiation: {sum(radiation.values()):.2f} kWh/m²/year")
    print(f"⚡ Plant Capacity: {total_power} kW")
    print(f"📦 Panel Type: {best_panel['name']}")
    print(f"📦 Number of Panels: {best_panel_count:.0f} panels")
    print(f"📈 Panel Efficiency: {best_efficiency*100:.1f}%")
    print(f"🔋 Annual Energy Production: {best_energy:,.2f} kWh/year")
    print(f"🔌 Grid Type: {grid_type.title()}")
    print("-" * 60)
    print("💰 ECONOMIC ANALYSIS")
    print(f"💵 Total Cost (USD): ${best_cost:,.2f}")

    if total_cost_local and total_cost_local_symbol:
        print(f"💵 Total Cost ({total_cost_local_symbol}): {total_cost_local_symbol}{total_cost_local:,.0f}")

    if annual_revenue_local and annual_revenue_usd:
        print(f"💶 Annual Revenue: {currency_symbol}{annual_revenue_local:,.2f} ({annual_revenue_usd:,.2f} USD)")

    if payback_years:
        print(f"📈 Payback Period: {payback_years:.1f} years")
        print(f"📊 ROI: {(1/payback_years * 100):.1f}% per year")
    print("=" * 60)

    print("\n📊 COMPARING SCENARIOS (On-Grid vs Off-Grid)...")
    scenarios = compare_scenarios(lat, lon, radiation, total_power, country_code)

    print("\n" + "=" * 60)
    print("📊 SCENARIO COMPARISON RESULTS")
    print("=" * 60)
    for gt, data in scenarios.items():
        print(f"\n🔌 {gt.upper()}:")
        print(f"   Panel: {data['panel']}")
        print(f"   Energy: {data['energy']:,.2f} kWh/year")
        print(f"   Cost: ${data['cost']:,.2f}")
        print(f"   Revenue: ${data['revenue']:,.2f}")
        if data['payback']:
            print(f"   Payback: {data['payback']:.1f} years")
        print(f"   ROI: {data['roi']:.1f}%")
    print("=" * 60)

    print("\n📊 SENSITIVITY ANALYSIS...")
    sensitivity_results = sensitivity_analysis(radiation, total_power, country_code)

    print("\n" + "=" * 60)
    print("📊 SENSITIVITY ANALYSIS RESULTS")
    print("=" * 60)
    print(f"{'Radiation Factor':<20} {'Energy (kWh)':<25} {'Revenue (USD)':<20}")
    print("-" * 60)
    for r in sensitivity_results:
        print(f"{r['radiation_factor']:<20.1f} {r['energy']:<25,.0f} ${r['revenue']:<20,.2f}")
    print("=" * 60)

    print("\n📊 Generating report with charts...")
    pdf_file = generate_pdf_report(
        radiation_data=radiation, total_energy=best_energy, total_power=total_power,
        panel_count=best_panel_count, panel_efficiency=best_efficiency * 100,
        total_cost=best_cost, annual_revenue=annual_revenue_usd if annual_revenue_usd else 0,
        payback_years=payback_years if payback_years else 0,
        country_name=country_name or country_code, location=location,
        grid_type=grid_type, panel_name=best_panel['name'],
        lat=lat, lon=lon, country_code=country_code
    )
    if pdf_file:
        print(f"✅ PDF report saved: {pdf_file}")

    normalized_production = best_energy / total_power
    theoretical_energy = best_energy / 0.85
    performance_ratio = (best_energy / theoretical_energy) * 100 if theoretical_energy > 0 else 0

    summary_data = {
        'Location': location, 'Country': country_name or country_code,
        'Total Power (kW)': total_power, 'Panel Type': best_panel['name'],
        'Panel Count': best_panel_count, 'Annual Energy (kWh)': best_energy,
        'Total Cost (USD)': best_cost,
        'Annual Revenue (USD)': annual_revenue_usd if annual_revenue_usd else 0,
        'Payback Period (years)': payback_years if payback_years else 0,
        'Performance Ratio (%)': performance_ratio,
        'Normalized Production (kWh/kWp)': normalized_production,
        'Grid Type': grid_type,
        'Latitude': lat, 'Longitude': lon,
        'PDF File': pdf_file
    }

    df_summary = pd.DataFrame([summary_data])
    csv_file = f"solar_summary_{location.replace(' ', '_')}.csv"
    df_summary.to_csv(csv_file, index=False)
    print(f"✅ Summary saved: {csv_file}")

    return {
        "location": location,
        "country": country_name or country_code,
        "total_power": total_power,
        "grid_type": grid_type,
        "panel": best_panel['name'],
        "panel_count": best_panel_count,
        "efficiency": best_efficiency,
        "energy": best_energy,
        "cost": best_cost,
        "revenue_usd": annual_revenue_usd if annual_revenue_usd else 0,
        "revenue_local": annual_revenue_local,
        "currency_symbol": currency_symbol,
        "payback": payback_years if payback_years else 0,
        "roi": (1/payback_years * 100) if payback_years else 0,
        "pdf_file": pdf_file,
        "csv_file": csv_file,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def save_last_simulation(last_result):
    if last_result is None:
        print("\n⚠️ No simulation to save! Run one first (option 1).")
        return

    print("\n" + "=" * 65)
    print("💾 SAVE LAST SIMULATION")
    print("=" * 65)

    custom_name = input("Enter a custom name for this simulation: ").strip()
    if not custom_name:
        print("❌ Name cannot be empty!")
        return

    safe_name = "".join(c for c in custom_name if c.isalnum() or c in "_- ").strip().replace(" ", "_")
    if not safe_name:
        print("❌ Invalid name!")
        return

    json_file = os.path.join(SAVED_DIR, f"{safe_name}.json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(last_result, f, indent=2, ensure_ascii=False)

    if last_result.get("pdf_file") and os.path.exists(last_result["pdf_file"]):
        custom_pdf = os.path.join(SAVED_DIR, f"{safe_name}.pdf")
        shutil.copy(last_result["pdf_file"], custom_pdf)
        print(f"✅ PDF copied to: {custom_pdf}")

    print(f"✅ Simulation saved as: {json_file}")
    print(f"📝 Name: {custom_name}")


def load_saved_simulation():
    print("\n" + "=" * 65)
    print("📂 LOAD SAVED SIMULATION")
    print("=" * 65)

    if not os.path.exists(SAVED_DIR):
        print("⚠️ No saved simulations found!")
        return

    saved_files = [f for f in os.listdir(SAVED_DIR) if f.endswith(".json")]
    if not saved_files:
        print("⚠️ No saved simulations found!")
        return

    print("\n📋 Available simulations:")
    for i, file in enumerate(saved_files, 1):
        print(f"  {i}. {file.replace('.json', '')}")

    try:
        choice = int(input("\nSelect simulation number: ").strip())
        if choice < 1 or choice > len(saved_files):
            print("❌ Invalid choice!")
            return

        selected_file = os.path.join(SAVED_DIR, saved_files[choice - 1])
        with open(selected_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        print("\n" + "=" * 65)
        print(f"📊 SIMULATION: {saved_files[choice-1].replace('.json', '')}")
        print("=" * 65)
        print(f"📍 Location: {data['location']}")
        print(f"🌍 Country: {data['country']}")
        print(f"⚡ Capacity: {data['total_power']} kW")
        print(f"🔌 Grid Type: {data['grid_type']}")
        print(f"📦 Panel: {data['panel']} × {data['panel_count']:.0f}")
        print(f"📈 Efficiency: {data['efficiency']*100:.1f}%")
        print(f"🔋 Energy: {data['energy']:,.0f} kWh/year")
        print(f"💵 Cost: ${data['cost']:,.2f}")
        print(f"💰 Revenue: ${data['revenue_usd']:,.2f}")
        print(f"📈 Payback: {data['payback']:.1f} years")
        print(f"📊 ROI: {data['roi']:.1f}%")
        print(f"⏰ Saved at: {data['timestamp']}")
        print("=" * 65)

    except ValueError:
        print("❌ Invalid input!")
    except Exception as e:
        print(f"❌ Error loading file: {e}")


def compare_saved_simulations():
    print("\n" + "=" * 65)
    print("📊 COMPARE SAVED SIMULATIONS")
    print("=" * 65)

    if not os.path.exists(SAVED_DIR):
        print("⚠️ No saved simulations found!")
        return

    saved_files = [f for f in os.listdir(SAVED_DIR) if f.endswith(".json")]
    if len(saved_files) < 2:
        print("⚠️ Need at least 2 saved simulations to compare!")
        return

    print("\n📋 Available simulations:")
    for i, file in enumerate(saved_files, 1):
        print(f"  {i}. {file.replace('.json', '')}")

    try:
        choices = input("\nEnter simulation numbers to compare (e.g., 1,2,3): ").strip()
        indices = [int(x.strip()) - 1 for x in choices.split(",")]

        if not all(0 <= i < len(saved_files) for i in indices):
            print("❌ Invalid choices!")
            return

        simulations = []
        for idx in indices:
            with open(os.path.join(SAVED_DIR, saved_files[idx]), "r", encoding="utf-8") as f:
                simulations.append(json.load(f))

        print("\n" + "=" * 100)
        print("📊 COMPARISON TABLE")
        print("=" * 100)
        print(f"{'Parameter':<25} " + " ".join([f"{'Sim ' + str(i+1):<20}" for i in range(len(simulations))]))
        print("-" * 100)

        rows = [
            ("Location", "location", ""),
            ("Capacity (kW)", "total_power", ".1f"),
            ("Grid Type", "grid_type", ""),
            ("Panel", "panel", ""),
            ("Panel Count", "panel_count", ".0f"),
            ("Energy (kWh/yr)", "energy", ",.0f"),
            ("Cost (USD)", "cost", ",.2f"),
            ("Revenue (USD)", "revenue_usd", ",.2f"),
            ("Payback (years)", "payback", ".1f"),
            ("ROI (%)", "roi", ".1f"),
        ]

        for label, key, fmt in rows:
            values = []
            for sim in simulations:
                val = sim.get(key, "N/A")
                if isinstance(val, (int, float)) and fmt:
                    values.append(f"{val:{fmt}}")
                else:
                    values.append(str(val)[:18])
            print(f"{label:<25} " + " ".join([f"{v:<20}" for v in values]))

        print("=" * 100)

        best_roi = max(simulations, key=lambda s: s.get("roi", 0))
        best_payback = min(simulations, key=lambda s: s.get("payback", float('inf')))
        print(f"\n🏆 Best ROI: {best_roi['location']} ({best_roi['roi']:.1f}%)")
        print(f"🏆 Best Payback: {best_payback['location']} ({best_payback['payback']:.1f} years)")

    except ValueError:
        print("❌ Invalid input! Use format: 1,2,3")
    except Exception as e:
        print(f"❌ Error: {e}")


def delete_saved_simulation():
    print("\n" + "=" * 65)
    print("🗑️  DELETE SAVED SIMULATION")
    print("=" * 65)

    if not os.path.exists(SAVED_DIR):
        print("⚠️ No saved simulations found!")
        return

    saved_files = [f for f in os.listdir(SAVED_DIR) if f.endswith(".json")]
    if not saved_files:
        print("⚠️ No saved simulations found!")
        return

    print("\n📋 Available simulations:")
    for i, file in enumerate(saved_files, 1):
        print(f"  {i}. {file.replace('.json', '')}")

    try:
        choice = int(input("\nSelect simulation number to DELETE: ").strip())
        if choice < 1 or choice > len(saved_files):
            print("❌ Invalid choice!")
            return

        selected_name = saved_files[choice - 1].replace('.json', '')

        confirm = input(f"\n⚠️ Are you sure you want to delete '{selected_name}'? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("❌ Deletion cancelled.")
            return

        json_file = os.path.join(SAVED_DIR, f"{selected_name}.json")
        if os.path.exists(json_file):
            os.remove(json_file)
            print(f"✅ Deleted JSON: {selected_name}.json")

        pdf_file = os.path.join(SAVED_DIR, f"{selected_name}.pdf")
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
            print(f"✅ Deleted PDF: {selected_name}.pdf")

        print(f"\n🗑️  Simulation '{selected_name}' deleted successfully!")

    except ValueError:
        print("❌ Invalid input!")
    except Exception as e:
        print(f"❌ Error deleting file: {e}")


def rename_saved_simulation():
    print("\n" + "=" * 65)
    print("✏️  RENAME SAVED SIMULATION")
    print("=" * 65)

    if not os.path.exists(SAVED_DIR):
        print("⚠️ No saved simulations found!")
        return

    saved_files = [f for f in os.listdir(SAVED_DIR) if f.endswith(".json")]
    if not saved_files:
        print("⚠️ No saved simulations found!")
        return

    print("\n📋 Available simulations:")
    for i, file in enumerate(saved_files, 1):
        print(f"  {i}. {file.replace('.json', '')}")

    try:
        choice = int(input("\nSelect simulation number to RENAME: ").strip())
        if choice < 1 or choice > len(saved_files):
            print("❌ Invalid choice!")
            return

        old_name = saved_files[choice - 1].replace('.json', '')

        new_name = input(f"Enter new name for '{old_name}': ").strip()
        if not new_name:
            print("❌ Name cannot be empty!")
            return

        safe_name = "".join(c for c in new_name if c.isalnum() or c in "_- ").strip().replace(" ", "_")
        if not safe_name:
            print("❌ Invalid name!")
            return

        new_json = os.path.join(SAVED_DIR, f"{safe_name}.json")
        if os.path.exists(new_json):
            print(f"❌ Name '{safe_name}' already exists! Please choose another name.")
            return

        old_json = os.path.join(SAVED_DIR, f"{old_name}.json")
        os.rename(old_json, new_json)
        print(f"✅ Renamed: {old_name}.json → {safe_name}.json")

        old_pdf = os.path.join(SAVED_DIR, f"{old_name}.pdf")
        new_pdf = os.path.join(SAVED_DIR, f"{safe_name}.pdf")
        if os.path.exists(old_pdf):
            os.rename(old_pdf, new_pdf)
            print(f"✅ Renamed: {old_name}.pdf → {safe_name}.pdf")

        print(f"\n✏️  Simulation renamed to '{safe_name}' successfully!")

    except ValueError:
        print("❌ Invalid input!")
    except Exception as e:
        print(f"❌ Error renaming file: {e}")


def main():
    show_banner()
    last_result = None

    while True:
        show_menu()
        choice = input("Enter your choice (1-7): ").strip()

        if choice == "1":
            result = run_simulation()
            if result:
                last_result = result
                print("\n✅ Simulation completed successfully!")
        elif choice == "2":
            save_last_simulation(last_result)
        elif choice == "3":
            load_saved_simulation()
        elif choice == "4":
            compare_saved_simulations()
        elif choice == "5":
            delete_saved_simulation()
        elif choice == "6":
            rename_saved_simulation()
        elif choice == "7":
            print("\n" + "=" * 65)
            print("👋 Thank you for using Solar Power Plant Simulator!")
            print("=" * 65)
            break
        else:
            print("❌ Invalid choice! Please enter a number between 1 and 7.")


if __name__ == "__main__":
    main()
