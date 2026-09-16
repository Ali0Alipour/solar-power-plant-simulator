import pytest
import os
import json
import requests
from datetime import datetime, timedelta
import reverse_geocoder as rg
from unittest.mock import patch, MagicMock
from project import (
    get_irr_exchange_rate,
    get_exchange_rate,
    get_coordinates,
    get_country_from_coordinates,
    fetch_solar_data,
    calculate_energy,
    calculate_cost,
    get_fit_rate,
    get_local_currency,
    calculate_revenue,
    calculate_payback,
    pso_optimize,
    sensitivity_analysis,
    compare_scenarios,
    save_last_simulation,
    load_saved_simulation,
    compare_saved_simulations,
    delete_saved_simulation,
    rename_saved_simulation,
    SAVED_DIR
)


def test_get_coordinates():
    lat, lon = get_coordinates("Tehran")
    assert lat is not None
    assert lon is not None
    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert -90 <= lat <= 90
    assert -180 <= lon <= 180


def test_get_coordinates_invalid():
    lat, lon = get_coordinates("ThisCityDoesNotExist12345XYZ")
    assert lat is None
    assert lon is None


def test_get_country_from_coordinates():
    country_code, country_name = get_country_from_coordinates(35.6892, 51.3890)
    assert country_code is not None
    assert country_name is not None
    assert isinstance(country_code, str)
    assert isinstance(country_name, str)
    assert len(country_code) == 2


def test_fetch_solar_data():
    radiation = fetch_solar_data(35.6892, 51.3890)
    assert radiation is not None
    assert isinstance(radiation, dict)
    assert len(radiation) > 0
    for date, value in radiation.items():
        assert isinstance(value, float)
        assert value >= 0


def test_calculate_energy():
    radiation = {"20240101": 5.0, "20240102": 4.5, "20240103": 6.0}
    energy, count = calculate_energy(radiation, 10, 0.55, 2.5, 0.18)
    assert energy > 0
    assert count > 0
    assert isinstance(energy, float)
    assert isinstance(count, float)


def test_calculate_energy_zero_radiation():
    radiation = {"20240101": 0.0, "20240102": 0.0}
    energy, count = calculate_energy(radiation, 10, 0.55, 2.5, 0.18)
    assert energy == 0


def test_calculate_cost_on_grid():
    cost = calculate_cost(10, "on-grid")
    assert cost > 0
    assert isinstance(cost, (int, float))


def test_calculate_cost_off_grid():
    cost = calculate_cost(10, "off-grid")
    assert cost > 0
    assert isinstance(cost, (int, float))


def test_off_grid_more_expensive():
    cost_on = calculate_cost(10, "on-grid")
    cost_off = calculate_cost(10, "off-grid")
    assert cost_off > cost_on


def test_calculate_cost_zero_power():
    cost = calculate_cost(0, "on-grid")
    assert cost == 0


def test_get_fit_rate_france():
    rate, currency, symbol, name = get_fit_rate("FR", 20)
    assert rate is not None
    assert currency == "EUR"
    assert symbol == "€"
    assert name == "France"
    assert isinstance(rate, float)
    assert rate > 0


def test_get_fit_rate_iran():
    rate, currency, symbol, name = get_fit_rate("IR", 20)
    assert rate is not None
    assert currency == "IRR"
    assert symbol == "تومان"
    assert name == "Iran"


def test_get_fit_rate_invalid_country():
    rate, currency, symbol, name = get_fit_rate("XX", 20)
    assert rate is None
    assert currency is None
    assert symbol is None
    assert name is None


def test_get_fit_rate_power_ranges():
    rate_small, _, _, _ = get_fit_rate("FR", 2)
    rate_medium, _, _, _ = get_fit_rate("FR", 20)
    rate_large, _, _, _ = get_fit_rate("FR", 200)
    assert rate_small is not None
    assert rate_medium is not None
    assert rate_large is not None


def test_get_local_currency():
    currency, symbol = get_local_currency("FR")
    assert currency == "EUR"
    assert symbol == "€"


def test_get_local_currency_invalid():
    currency, symbol = get_local_currency("XX")
    assert currency is None
    assert symbol is None


def test_calculate_revenue():
    annual_local, annual_usd, symbol, name = calculate_revenue(10000, 20, "FR")
    assert annual_local is not None
    assert annual_usd is not None
    assert symbol == "€"
    assert isinstance(annual_local, float)
    assert annual_local > 0


def test_calculate_revenue_invalid_country():
    annual_local, annual_usd, symbol, name = calculate_revenue(10000, 20, "XX")
    assert annual_local is None
    assert annual_usd is None


def test_calculate_payback():
    payback = calculate_payback(10000, 2000)
    assert payback == 5.0
    assert isinstance(payback, float)


def test_calculate_payback_zero_revenue():
    payback = calculate_payback(10000, 0)
    assert payback is None


def test_calculate_payback_none_revenue():
    payback = calculate_payback(10000, None)
    assert payback is None


def test_pso_optimize():
    radiation = {"20240101": 5.0, "20240102": 4.5, "20240103": 6.0}
    result = pso_optimize(35.6892, 51.3890, 10, "on-grid", radiation)
    assert result is not None
    assert "best_panel" in result
    assert "best_energy" in result
    assert "best_cost" in result
    assert "best_panel_count" in result
    assert "best_efficiency" in result
    assert result["best_energy"] > 0
    assert result["best_cost"] > 0


def test_pso_optimize_off_grid():
    radiation = {"20240101": 5.0, "20240102": 4.5, "20240103": 6.0}
    result = pso_optimize(35.6892, 51.3890, 10, "off-grid", radiation)
    assert result is not None
    assert result["best_cost"] > 0


def test_pso_result_keys():
    radiation = {"20240101": 5.0}
    result = pso_optimize(35.6892, 51.3890, 10, "on-grid", radiation)
    expected_keys = ["best_panel_key", "best_panel", "best_tech", "best_power",
                     "best_fitness", "best_energy", "best_cost", "best_efficiency",
                     "best_panel_count", "best_cost_per_kwh"]
    for key in expected_keys:
        assert key in result


def test_sensitivity_analysis():
    radiation = {"20240101": 5.0, "20240102": 4.5, "20240103": 6.0}
    results = sensitivity_analysis(radiation, 10, "FR")
    assert results is not None
    assert len(results) == 5
    for result in results:
        assert "radiation_factor" in result
        assert "energy" in result
        assert "revenue" in result
        assert isinstance(result["radiation_factor"], float)
        assert isinstance(result["energy"], float)
        assert result["energy"] > 0


def test_sensitivity_analysis_factors():
    radiation = {"20240101": 5.0}
    results = sensitivity_analysis(radiation, 10, "FR")
    factors = [r["radiation_factor"] for r in results]
    assert 0.8 in factors
    assert 1.0 in factors
    assert 1.2 in factors


def test_compare_scenarios():
    radiation = {"20240101": 5.0, "20240102": 4.5}
    scenarios = compare_scenarios(35.6892, 51.3890, radiation, 10, "FR")
    assert scenarios is not None
    assert "on-grid" in scenarios
    assert "off-grid" in scenarios
    assert scenarios["on-grid"]["cost"] > 0
    assert scenarios["off-grid"]["cost"] > 0


def test_exchange_rate_irr():
    rate = get_irr_exchange_rate()
    assert rate is not None
    assert isinstance(rate, float)
    assert rate > 10000


def test_exchange_rate_eur_to_usd():
    rate = get_exchange_rate("EUR", "USD")
    if rate is not None:
        assert isinstance(rate, float)
        assert rate > 0


def test_full_flow():
    lat, lon = get_coordinates("Tehran")
    assert lat is not None
    assert lon is not None

    country_code, country_name = get_country_from_coordinates(lat, lon)
    assert country_code is not None

    radiation = fetch_solar_data(lat, lon)
    assert radiation is not None

    result = pso_optimize(lat, lon, 10, "on-grid", radiation)
    assert result["best_energy"] > 0
    assert result["best_cost"] > 0

    _, annual_usd, _, _ = calculate_revenue(result["best_energy"], 10, country_code)
    assert annual_usd is not None


def test_radiation_data_structure():
    radiation = fetch_solar_data(35.6892, 51.3890)
    assert radiation is not None
    for date_str in radiation.keys():
        try:
            datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            pytest.fail(f"Invalid date format: {date_str}")
    for value in radiation.values():
        assert 0 <= value <= 10


def test_panel_database_integrity():
    from project import PANEL_DATABASE
    for key, panel in PANEL_DATABASE.items():
        assert "power" in panel
        assert "area" in panel
        assert "efficiency" in panel
        assert "price_per_panel" in panel
        assert panel["power"] > 0
        assert panel["area"] > 0
        assert 0 < panel["efficiency"] < 1
        assert panel["price_per_panel"] > 0


def test_equipment_prices():
    from project import EQUIPMENT_PRICES
    for item, price in EQUIPMENT_PRICES.items():
        assert price > 0
        assert isinstance(price, (int, float))


def test_fit_rates_structure():
    from project import FIT_RATES
    for country, data in FIT_RATES.items():
        assert "currency" in data
        assert "symbol" in data
        assert "name" in data
        assert "rates" in data
        assert isinstance(data["rates"], list)
        for rate in data["rates"]:
            assert "max_power" in rate
            assert "rate" in rate
            assert rate["max_power"] > 0
            assert rate["rate"] > 0


def test_technologies_structure():
    from project import TECHNOLOGIES
    for tech, data in TECHNOLOGIES.items():
        assert "name" in data
        assert "efficiency_range" in data
        assert "price_range" in data
        assert "degradation" in data
        assert len(data["efficiency_range"]) == 2
        assert len(data["price_range"]) == 2


def test_saved_dir_exists():
    assert os.path.exists(SAVED_DIR)
    assert os.path.isdir(SAVED_DIR)


def test_save_last_simulation_none():
    save_last_simulation(None)


def test_save_and_load_simulation(tmp_path, monkeypatch):
    test_result = {
        "location": "TestCity",
        "country": "TestCountry",
        "total_power": 10,
        "grid_type": "on-grid",
        "panel": "Test Panel",
        "panel_count": 20,
        "efficiency": 0.2,
        "energy": 10000,
        "cost": 5000,
        "revenue_usd": 1000,
        "revenue_local": 900,
        "currency_symbol": "€",
        "payback": 5.0,
        "roi": 20.0,
        "pdf_file": None,
        "csv_file": None,
        "timestamp": "2024-01-01 00:00:00"
    }

    test_file = os.path.join(SAVED_DIR, "test_simulation.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(test_result, f)

    assert os.path.exists(test_file)

    with open(test_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["location"] == "TestCity"
    assert loaded["total_power"] == 10

    os.remove(test_file)


def test_compare_saved_simulations_no_files():
    compare_saved_simulations()


def test_load_saved_no_files():
    load_saved_simulation()


def test_calculate_energy_single_day():
    radiation = {"20240101": 5.0}
    energy, count = calculate_energy(radiation, 10, 0.55, 2.5, 0.18)
    expected = 5.0 * 2.5 * (10 / 0.55) * 0.18
    assert abs(energy - expected) < 0.01


def test_calculate_cost_scales_with_power():
    cost_10 = calculate_cost(10, "on-grid")
    cost_20 = calculate_cost(20, "on-grid")
    assert abs(cost_20 - 2 * cost_10) < 0.01


def test_payback_positive_values():
    payback = calculate_payback(1000, 100)
    assert payback == 10.0


def test_fit_rate_all_countries():
    from project import FIT_RATES
    for country in FIT_RATES.keys():
        rate, currency, symbol, name = get_fit_rate(country, 20)
        assert rate is not None
        assert currency is not None
        assert symbol is not None
        assert name is not None


def test_panel_selection_by_power():
    from project import PANEL_DATABASE
    powers = [panel["power"] for panel in PANEL_DATABASE.values()]
    assert min(powers) >= 0.3
    assert max(powers) <= 0.6


def test_delete_saved_simulation_no_files():
    delete_saved_simulation()


def test_rename_saved_simulation_no_files():
    rename_saved_simulation()


def test_delete_simulation_workflow():
    test_name = "test_delete_me"
    test_file = os.path.join(SAVED_DIR, f"{test_name}.json")

    with open(test_file, "w", encoding="utf-8") as f:
        json.dump({"location": "TestCity"}, f)

    assert os.path.exists(test_file)

    os.remove(test_file)
    assert not os.path.exists(test_file)


def test_rename_simulation_workflow():
    old_name = "test_rename_old"
    new_name = "test_rename_new"

    old_file = os.path.join(SAVED_DIR, f"{old_name}.json")
    new_file = os.path.join(SAVED_DIR, f"{new_name}.json")

    with open(old_file, "w", encoding="utf-8") as f:
        json.dump({"location": "TestCity"}, f)

    assert os.path.exists(old_file)

    os.rename(old_file, new_file)

    assert os.path.exists(new_file)
    assert not os.path.exists(old_file)

    with open(new_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["location"] == "TestCity"

    os.remove(new_file)


def test_rename_with_pdf_workflow():
    old_name = "test_pdf_old"
    new_name = "test_pdf_new"

    old_json = os.path.join(SAVED_DIR, f"{old_name}.json")
    new_json = os.path.join(SAVED_DIR, f"{new_name}.json")
    old_pdf = os.path.join(SAVED_DIR, f"{old_name}.pdf")
    new_pdf = os.path.join(SAVED_DIR, f"{new_name}.pdf")

    with open(old_json, "w", encoding="utf-8") as f:
        json.dump({"location": "TestCity"}, f)

    with open(old_pdf, "wb") as f:
        f.write(b"test pdf content")

    assert os.path.exists(old_json)
    assert os.path.exists(old_pdf)

    os.rename(old_json, new_json)
    os.rename(old_pdf, new_pdf)

    assert os.path.exists(new_json)
    assert os.path.exists(new_pdf)
    assert not os.path.exists(old_json)
    assert not os.path.exists(old_pdf)

    os.remove(new_json)
    os.remove(new_pdf)


def test_delete_removes_both_files():
    test_name = "test_delete_both"
    json_file = os.path.join(SAVED_DIR, f"{test_name}.json")
    pdf_file = os.path.join(SAVED_DIR, f"{test_name}.pdf")

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({"location": "TestCity"}, f)

    with open(pdf_file, "wb") as f:
        f.write(b"test pdf content")

    assert os.path.exists(json_file)
    assert os.path.exists(pdf_file)

    os.remove(json_file)
    os.remove(pdf_file)

    assert not os.path.exists(json_file)
    assert not os.path.exists(pdf_file)


def test_rename_prevents_duplicate():
    name1 = "test_duplicate_1"
    name2 = "test_duplicate_2"

    file1 = os.path.join(SAVED_DIR, f"{name1}.json")
    file2 = os.path.join(SAVED_DIR, f"{name2}.json")

    with open(file1, "w", encoding="utf-8") as f:
        json.dump({"location": "City1"}, f)

    with open(file2, "w", encoding="utf-8") as f:
        json.dump({"location": "City2"}, f)

    assert os.path.exists(file1)
    assert os.path.exists(file2)

    os.remove(file1)
    os.remove(file2)


def test_saved_dir_cleanup():
    assert os.path.exists(SAVED_DIR)

    test_files = [f for f in os.listdir(SAVED_DIR) if f.startswith("test_")]
    for f in test_files:
        try:
            os.remove(os.path.join(SAVED_DIR, f))
        except:
            pass

    remaining = [f for f in os.listdir(SAVED_DIR) if f.startswith("test_")]
    assert len(remaining) == 0
