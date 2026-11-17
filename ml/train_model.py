import pandas as pd
from ingestion.db import get_engine
from sklearn.metrics import mean_absolute_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

FEATURES = ["wind_lag1", "wind_lag2"]
TARGET = "wind_electricity"
CHANGE_FEATURES = ["change_lag1"]
TEST_START_YEAR = 2019


def load_data():
    engine = get_engine()
    query = """
        select country, year, wind_electricity
        from staging.stg_energy
        order by country, year
    """
    return pd.read_sql(query, engine)


def add_features(df):
    df = df.copy()
    df["wind_lag1"] = df.groupby("country")["wind_electricity"].shift(1)
    df["wind_lag2"] = df.groupby("country")["wind_electricity"].shift(2)
    df["change_lag1"] = df["wind_lag1"] - df["wind_lag2"]
    df["change"] = df["wind_electricity"] - df["wind_lag1"]
    return df


def split_by_time(df):
    df = df.dropna(subset=["wind_electricity", "wind_lag1", "wind_lag2"])
    train = df[df["year"] < TEST_START_YEAR]
    test = df[df["year"] >= TEST_START_YEAR]
    return train, test


def evaluate(model, train, test):
    model.fit(train[FEATURES], train[TARGET])
    predictions = model.predict(test[FEATURES])
    return mean_absolute_error(test[TARGET], predictions)


def evaluate_change(model, train, test):
    model.fit(train[CHANGE_FEATURES], train["change"])
    predicted_change = model.predict(test[CHANGE_FEATURES])
    predictions = test["wind_lag1"] + predicted_change
    return mean_absolute_error(test[TARGET], predictions)


def forecast_next_year(df):                                               # NEW
    data = df.dropna(subset=["change", "change_lag1"])

    model = LinearRegression()
    model.fit(data[CHANGE_FEATURES], data["change"])

    latest = df[df["year"] == df["year"].max()].copy()
    latest["change_lag1"] = latest["wind_electricity"] - latest["wind_lag1"]
    predicted_change = model.predict(latest[CHANGE_FEATURES])

    forecast = pd.DataFrame({
        "country": latest["country"],
        "forecast_year": latest["year"] + 1,
        "forecast_wind_twh": (latest["wind_electricity"] + predicted_change).round(2),
    })
    return forecast


def save_forecast(forecast):                                              # NEW
    engine = get_engine()
    forecast.to_sql("wind_forecast", engine, schema="ml", if_exists="replace", index=False)


if __name__ == "__main__":
    df = add_features(load_data())
    train, test = split_by_time(df)

    print(f"Train: {len(train)} rows, {train['year'].min()}-{train['year'].max()}")
    print(f"Test:  {len(test)} rows, {test['year'].min()}-{test['year'].max()}")

    baseline_mae = mean_absolute_error(test["wind_electricity"], test["wind_lag1"])
    print(f"Baseline MAE (next year = this year): {baseline_mae:.2f} TWh")

    models = [
        ("Linear regression", LinearRegression()),
        ("Random forest", RandomForestRegressor(n_estimators=200, random_state=42)),
    ]

    print("\nPredicting the level:")
    for name, model in models:
        mae = evaluate(model, train, test)
        print(f"  {name} MAE: {mae:.2f} TWh")

    print("\nPredicting the change:")
    for name, model in models:
        mae = evaluate_change(model, train, test)
        print(f"  {name} MAE: {mae:.2f} TWh")

    forecast = forecast_next_year(df)                                     # NEW
    save_forecast(forecast)                                               # NEW
    print("\nForecast saved to ml.wind_forecast:")                         # NEW
    print(forecast.to_string(index=False))                                # NEW