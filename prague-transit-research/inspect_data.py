import pandas as pd

# Load cleaned data
df = pd.read_csv("data/vehicle_data_clean.csv")

print("\n--- BASIC INFORMATION ---")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

print("\n--- COLUMNS ---")
print(df.columns.tolist())

print("\n--- MODES ---")
print(df["mode"].value_counts())

print("\n--- ROUTES ---")
print(df["route"].value_counts().head(20))

print("\n--- DELAY ---")
print(df["delay_seconds"].describe())

print("\n--- STATUS ---")
print(df["status"].value_counts())

print("\n--- UNIQUE VEHICLES ---")
print(df["vehicle_id"].nunique())

print("\n--- UNIQUE TRIPS ---")
print(df["trip_id"].nunique())

print("\n--- MISSING VALUES ---")
print(df.isnull().sum())