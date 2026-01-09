import json
import pandas as pd
import numpy as np

JSON_PATH = "static/data/bengaluru_area_temperatures.json"
CSV_PATH  = "static/data/historical_yearly_aqi.csv"
OUT_PATH  = "static/data/bengaluru_with_pollution.json"

with open(JSON_PATH) as f:
    data = json.load(f)

df = pd.read_csv(CSV_PATH)

# normalize area names
df["area_norm"] = df["area"].str.strip().str.lower()

# backcast multipliers
multipliers = {
    2019: 1.10,
    2018: 1.00,
    2017: 0.92,
    2016: 0.85,
    2015: 0.78
}

# AQI table
AQI_TABLE = {
    "so2": [(0,20),(20,80),(80,250),(250,350),(350,None)],
    "no2": [(0,40),(40,70),(70,150),(150,200),(200,None)],
    "pm10":[(0,20),(20,50),(50,100),(100,200),(200,None)],
    "pm25":[(0,10),(10,25),(25,50),(50,75),(75,None)],
    "o3":  [(0,60),(60,100),(100,140),(140,180),(180,None)],
    "co":  [(0,4400),(4400,9400),(9400,12400),(12400,15400),(15400,None)]
}

def classify(val, ranges):
    for i,(lo,hi) in enumerate(ranges,1):
        if hi is None:
            if val >= lo:
                return i
        else:
            if lo <= val < hi:
                return i
    return 1

for year in data:
    y = int(year)
    for district in data[year]:
        key = district.strip().lower()

        rows = df[(df["area_norm"] == key) & (df["year"] == 2020)]
        if rows.empty:
            continue

        base = rows.iloc[0]

        if y >= 2020:
            src = df[(df["area_norm"] == key) & (df["year"] == y)]
            if src.empty:
                continue
            base = src.iloc[0]
            factor = 1
        else:
            factor = multipliers[y]

        noise = np.random.uniform(0.9, 1.1)

        pollutants = {
            "pm25": base["pm2_5_avg"] * factor * noise,
            "pm10": base["pm10_avg"]  * factor * noise,
            "no2":  base["no2_avg"]   * factor * noise,
            "so2":  0.3 * base["no2_avg"] * factor * noise,
            "o3":   base["o3_avg"]    * factor * noise,
            "co":   base["co_avg"]    * factor * noise
        }

        aqi = max([
            classify(pollutants["so2"],  AQI_TABLE["so2"]),
            classify(pollutants["no2"],  AQI_TABLE["no2"]),
            classify(pollutants["pm10"], AQI_TABLE["pm10"]),
            classify(pollutants["pm25"], AQI_TABLE["pm25"]),
            classify(pollutants["o3"],   AQI_TABLE["o3"]),
            classify(pollutants["co"],   AQI_TABLE["co"])
        ])

        data[year][district]["pollutants"] = pollutants
        data[year][district]["aqi"] = aqi

with open(OUT_PATH,"w") as f:
    json.dump(data,f,indent=2)

print("Saved:", OUT_PATH)
