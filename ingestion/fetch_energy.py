import pandas as pd
from datetime import datetime
from sqlalchemy import text                 # NEW
from ingestion.db import get_engine         # NEW

URL = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
import pandas as pd
from datetime import datetime

URL = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"

COUNTRIES = [
    "Germany", "France", "Spain", "Italy", "Poland", "Netherlands",
    "Belgium", "Sweden", "Norway", "Denmark", "Austria", "Portugal",
]

COLUMNS = [
    "country", "year", "electricity_generation",
    "renewables_electricity", "wind_electricity", "solar_electricity",
]

df = pd.read_csv(URL)

df = df[df["country"].isin(COUNTRIES)]
df = df[df["year"] >= 2000]
df = df[COLUMNS].copy()
df["ingested_at"] = datetime.now()

print(df.shape)
print(df.head())

 
engine = get_engine()

with engine.begin() as conn:
    conn.execute(text("DELETE FROM raw.energy"))
    df.to_sql("energy", conn, schema="raw", if_exists="append", index=False)

print(f"Loaded {len(df)} rows into raw.energy")