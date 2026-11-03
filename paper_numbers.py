"""
Derive every number used in Sections 4-6 of the paper from the four result
tables written by analyze_costs.py, plus the external inputs documented below.

Usage:  python paper_numbers.py <results_dir> [output.json]
"""
import glob
import json
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

results_dir = Path(sys.argv[1])
out_json = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("numbers.json")


def load(suffix, index_col=0):
    f = sorted(glob.glob(str(results_dir / f"*{suffix}")))
    if not f:
        raise SystemExit(f"missing *{suffix} in {results_dir}")
    df = pd.read_csv(f[-1], index_col=index_col)
    df.index = df.index.astype(str)
    return df


by_route = load("table_descriptive_by_route.csv")
by_time = load("table_descriptive_by_time.csv")
trip = load("table_descriptive_trip_level.csv")
cost = load("table_cost.csv", index_col="route")

LINES = ["9", "17", "22"]

# ---------------------------------------------------------------- parameters
# Parameters of analyze_costs.py, recovered from table_cost.csv and checked below.
VOR_MULT = 0.54
TRIPS_PER_DAY = 2
DAYS_PER_YEAR = 220
TRIPS_PER_YEAR = TRIPS_PER_DAY * DAYS_PER_YEAR
vot_implied = (cost.loc["17", "cost_trip_CZK"] * 60
               / (cost.loc["17", "T_add_min"] + VOR_MULT * cost.loc["17", "sigma_min"]))
VOT = round(vot_implied, 1)
for r in LINES + ["All"]:
    c = VOT / 60 * (cost.loc[r, "T_add_min"] + VOR_MULT * cost.loc[r, "sigma_min"])
    assert abs(c - cost.loc[r, "cost_trip_CZK"]) < 0.01, (r, c)
    assert abs(cost.loc[r, "cost_trip_CZK"] * TRIPS_PER_YEAR
               - cost.loc[r, "cost_year_CZK"]) < 1, r

# Czech stated-preference estimates, bus (Maca & Kohlova 2019, Table 4; ~2011 prices)
CZ_BUS_VOT, CZ_BUS_VOR = 74.0, 40.0
# External ridership inputs (see paper Table 12)
PAX_2016 = {"22": 118075, "9": 101226, "17": 53924}   # PID tram survey, 2016
NETWORK_2016 = 1069863                                 # all tram lines, working day 06-23h
DPP_TRAM_2025 = 368_000_000                            # "more than 368 million"
WORKING_DAYS = 250
POP_PRAGUE = 1_407_084                                 # CZSO, 31 Dec 2025 (preliminary)
WAGE_NATIONAL, WAGE_PRAGUE, HOURS_PER_MONTH = 49402, 62307, 168

# ---------------------------------------------------------------- spreads
sigma_sd = {r: float(by_route.loc[r, "sd"]) for r in LINES + ["All"]}
sigma_rob = {r: float(by_route.loc[r, "iqr"]) / 1.349 for r in LINES + ["All"]}
t_add = {r: float(cost.loc[r, "T_add_min"]) for r in LINES + ["All"]}

share3 = {l: PAX_2016[l] / sum(PAX_2016.values()) for l in LINES}
trips_m2 = {l: DPP_TRAM_2025 * PAX_2016[l] / NETWORK_2016 for l in LINES}   # central
trips_m1 = {l: PAX_2016[l] * WORKING_DAYS for l in LINES}                   # low

SCEN = {
    "S1": dict(label="As computed", vot=VOT, vor=VOR_MULT * VOT, spread="SD"),
    "S2": dict(label="As computed, robust spread", vot=VOT, vor=VOR_MULT * VOT, spread="IQR"),
    "S3": dict(label="Czech bus values", vot=CZ_BUS_VOT, vor=CZ_BUS_VOR, spread="SD"),
    "S4": dict(label="Czech bus values, robust spread", vot=CZ_BUS_VOT, vor=CZ_BUS_VOR, spread="IQR"),
    "S5": dict(label="Time cost only", vot=VOT, vor=0.0, spread="SD"),
}
scen_out = {}
for k, s in SCEN.items():
    sig = sigma_sd if s["spread"] == "SD" else sigma_rob
    per_line = {l: s["vot"] / 60 * t_add[l] + s["vor"] / 60 * sig[l] for l in LINES}
    pooled = s["vot"] / 60 * t_add["All"] + s["vor"] / 60 * sig["All"]
    weighted = sum(share3[l] * per_line[l] for l in LINES)
    agg_m2 = sum(per_line[l] * trips_m2[l] for l in LINES)
    agg_m1 = sum(per_line[l] * trips_m1[l] for l in LINES)
    scen_out[k] = dict(
        **s, per_line=per_line, pooled=pooled, weighted=weighted,
        annual_commuter=weighted * TRIPS_PER_YEAR,
        agg_m2=agg_m2, agg_m1=agg_m1,
        per_resident=agg_m2 / POP_PRAGUE,
        agg_by_line_m2={l: per_line[l] * trips_m2[l] for l in LINES},
    )

# headline cost split (S1) into time and reliability parts
split = {}
for r in LINES + ["All"]:
    time_part = VOT / 60 * t_add[r]
    rel_part = VOR_MULT * VOT / 60 * sigma_sd[r]
    split[r] = dict(time=time_part, rel=rel_part, rel_share=rel_part / (time_part + rel_part))

# hours of extra time per year (T_add * trips)
hours_year = {r: t_add[r] * TRIPS_PER_YEAR / 60 for r in LINES + ["All"]}

# ---------------------------------------------------------------- trip-level inference
ci = {}
for r in LINES + ["All"]:
    n, m, sd = trip.loc[r, "n"], trip.loc[r, "mean"], trip.loc[r, "sd"]
    se = sd / n ** 0.5
    h = stats.t.ppf(0.975, n - 1) * se
    ci[r] = [m - h, m + h]


def welch(a, b):
    t, p = stats.ttest_ind_from_stats(trip.loc[a, "mean"], trip.loc[a, "sd"], trip.loc[a, "n"],
                                      trip.loc[b, "mean"], trip.loc[b, "sd"], trip.loc[b, "n"],
                                      equal_var=False)
    return dict(diff=float(trip.loc[a, "mean"] - trip.loc[b, "mean"]), t=float(t), p=float(p))


tests = {"22_vs_9": welch("22", "9"), "17_vs_9": welch("17", "9"), "22_vs_17": welch("22", "17")}

out = dict(
    params=dict(VOT=VOT, VOR_MULT=VOR_MULT, VOR=VOR_MULT * VOT, TRIPS_PER_DAY=TRIPS_PER_DAY,
                DAYS_PER_YEAR=DAYS_PER_YEAR, TRIPS_PER_YEAR=TRIPS_PER_YEAR,
                CZ_BUS_VOT=CZ_BUS_VOT, CZ_BUS_VOR=CZ_BUS_VOR, WORKING_DAYS=WORKING_DAYS,
                POP_PRAGUE=POP_PRAGUE, DPP_TRAM_2025=DPP_TRAM_2025, NETWORK_2016=NETWORK_2016,
                PAX_2016=PAX_2016,
                wage_hourly_national=WAGE_NATIONAL / HOURS_PER_MONTH,
                wage_hourly_prague=WAGE_PRAGUE / HOURS_PER_MONTH,
                vot_vs_national_wage=VOT / (WAGE_NATIONAL / HOURS_PER_MONTH)),
    by_route=by_route.to_dict("index"), by_time=by_time.to_dict("index"),
    trip=trip.to_dict("index"), cost=cost.to_dict("index"),
    sigma_sd=sigma_sd, sigma_rob=sigma_rob, t_add=t_add,
    share3=share3, share_3lines_of_network=sum(PAX_2016.values()) / NETWORK_2016,
    pax_3lines_day=sum(PAX_2016.values()),
    trips_m2=trips_m2, trips_m1=trips_m1,
    trips_m2_total=sum(trips_m2.values()), trips_m1_total=sum(trips_m1.values()),
    scen=scen_out, split=split, hours_year=hours_year, ci=ci, tests=tests,
    n_obs=int(by_route.loc["All", "n"]), n_trips=int(trip.loc["All", "n"]),
    snaps_per_trip=float(by_route.loc["All", "n"] / trip.loc["All", "n"]),
    tram_share_of_dpp=DPP_TRAM_2025 / 998.1e6,
)
out_json.write_text(json.dumps(out, indent=1, default=float))

# ---------------------------------------------------------------- print summary
print(f"VOT recovered from table_cost.csv: {vot_implied:.3f} -> {VOT} CZK/h (VOR {VOR_MULT*VOT:.0f})")
print(f"trips/yr per commuter {TRIPS_PER_YEAR}; line shares of 3 lines:", {k: round(v, 4) for k, v in share3.items()})
print(f"3 lines = {out['share_3lines_of_network']:.4f} of 2016 network; annual trips M2 {out['trips_m2_total']/1e6:.1f}M, M1 {out['trips_m1_total']/1e6:.1f}M")
for k, s in scen_out.items():
    print(f"{k} {s['label']:34s} pooled {s['pooled']:6.2f} weighted {s['weighted']:6.2f} "
          f"commuter/yr {s['annual_commuter']:8.0f}  agg M2 {s['agg_m2']/1e6:7.1f}M  agg M1 {s['agg_m1']/1e6:7.1f}M  per resident {s['per_resident']:6.0f}")
    print("     per line:", {l: round(v, 2) for l, v in s["per_line"].items()})
print("S1 split:", {r: (round(v['time'], 2), round(v['rel'], 2), round(v['rel_share'], 3)) for r, v in split.items()})
print("hours/yr:", {r: round(v, 1) for r, v in hours_year.items()})
print("robust sigma:", {r: round(v, 3) for r, v in sigma_rob.items()}, " SD:", {r: round(v, 3) for r, v in sigma_sd.items()})
print("CI trip mean:", {r: [round(x, 2) for x in v] for r, v in ci.items()})
print("Welch:", {k: {a: round(b, 3) for a, b in v.items()} for k, v in tests.items()})
print("wage-hourly national/prague:", round(WAGE_NATIONAL / HOURS_PER_MONTH, 1), round(WAGE_PRAGUE / HOURS_PER_MONTH, 1), " VOT/national:", round(out['params']['vot_vs_national_wage'], 2))
print("snapshots per trip:", round(out["snaps_per_trip"], 1), " tram share of DPP:", round(out["tram_share_of_dpp"], 3))