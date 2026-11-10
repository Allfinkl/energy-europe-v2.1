import requests
import pandas as pd
from sqlalchemy import text
from ingestion.db import get_engine
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = "https://api.open-meteo.com/v1/forecast"

LOCATIONS = {
    "Germany":     {"lat": 52.52, "lon": 13.41},
    "France":      {"lat": 48.85, "lon": 2.35},
    "Spain":       {"lat": 40.42, "lon": -3.70},
    "Italy":       {"lat": 41.90, "lon": 12.50},
    "Poland":      {"lat": 52.23, "lon": 21.01},
    "Netherlands": {"lat": 52.37, "lon": 4.90},
    "Belgium":     {"lat": 50.85, "lon": 4.35},
    "Sweden":      {"lat": 59.33, "lon": 18.07},
    "Norway":      {"lat": 59.91, "lon": 10.75},
    "Denmark":     {"lat": 55.68, "lon": 12.57},
    "Austria":     {"lat": 48.21, "lon": 16.37},
    "Portugal":    {"lat": 38.72, "lon": -9.14},
}


def make_session():
    session = requests.Session()
    retries = Retry(total=4, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def fetch_country(session, country, lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "wind_speed_10m_max,shortwave_radiation_sum,precipitation_sum",
        "forecast_days": 7,
        "timezone": "Europe/Berlin",
    }
    response = session.get(URL, params=params, timeout=30)
    response.raise_for_status()

    daily = pd.DataFrame(response.json()["daily"])
    daily["country"] = country
    return daily


session = make_session()
frames = []

for country, loc in LOCATIONS.items():
    try:
        frames.append(fetch_country(session, country, loc["lat"], loc["lon"]))
        print(f"{country} fetched")
    except requests.RequestException as e:
        print(f"{country} FAILED, skipping: {e}")

if not frames:
    raise SystemExit("No weather data fetched at all. Stopping.")

df = pd.concat(frames, ignore_index=True)
df = df.rename(columns={
    "time": "forecast_date",
    "wind_speed_10m_max": "wind_speed_max_kmh",
    "shortwave_radiation_sum": "solar_radiation_mj",
    "precipitation_sum": "precipitation_mm",
})
df["ingested_at"] = datetime.now()

print(df.shape)
print(df.head())

df["forecast_date"] = pd.to_datetime(df["forecast_date"]).dt.date

fetched = df["country"].unique().tolist()

engine = get_engine()
with engine.begin() as conn:
    conn.execute(
        text("DELETE FROM raw.weather WHERE country = ANY(:countries)"),
        {"countries": fetched},
    )
    df.to_sql("weather", conn, schema="raw", if_exists="append", index=False)

print(f"Loaded {len(df)} rows for {len(fetched)} countries into raw.weather")