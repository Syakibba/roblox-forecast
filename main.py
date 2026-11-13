#!/usr/bin/env python3
"""roblox-up-and-coming-forecast-01: empirical rank-transition forecaster.
Reads /input/history.ndjson + /input/task.json, writes /output/forecast.json.
Forecasts hourly charts for the 72h window by applying the chart's own
observed rank-transition statistics (with recency weighting and Laplace
smoothing) to the last snapshot's chart, then normalizing per place."""
import json, math, os, collections

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
PLACES_DEFAULT = 10
BAND = 2          # ranks of transition band each side
RECENT_N = 6      # only the most recent transitions count extra
EPS = 1e-4

def rank_maps(s):
    return {g["universe_id"]: g["rank"] for g in s.get("up_and_coming", []) if g.get("rank")}

def build_counts(snaps):
    counts = collections.defaultdict(collections.Counter)
    n = len(snaps)
    for i in range(len(snaps) - 1):
        ra, rb = rank_maps(snaps[i]), rank_maps(snaps[i + 1])
        # recency weight: later transitions matter more (exponential)
        w = 2.0 ** ((i - max(0, len(snaps) - 1 - RECENT_N)) / 2.0) if i >= len(snaps) - 1 - RECENT_N else 1.0
        w = max(w, 1.0)
        for u, r in ra.items():
            counts[r][rb.get(u, 0)] += w
    return counts

def forecast(snaps, places):
    last = snaps[-1]
    ranks = rank_maps(last)
    counts = build_counts(snaps)
    # per place: p(game g at place k) proportional to smoothed P(r -> k) ; blend with
    # a light "neighbors" prior like the house baseline for stability.
    place_probs = {k: collections.defaultdict(float) for k in range(1, places + 1)}
    for u, r in ranks.items():
        cnt = counts.get(r, collections.Counter())
        tot = sum(cnt.values())
        for k in range(1, places + 1):
            if tot:
                band = sum(cnt[kk] for kk in range(max(1, k - BAND), k + BAND + 1))
                emp = (band + 0.5) / (tot + 3.0)
            else:
                emp = 0.1
            # spread band mass over the (2B+1) places, plus house-style prior
            prior = 0.0
            if r == k: prior += 0.5
            if r == k - 1 and k > 1: prior += 0.15
            if r == k + 1: prior += 0.3 if k == 1 else 0.15
            place_probs[k][u] += 0.65 * emp / (2 * BAND + 1) + 0.35 * prior
    # unnamed mass over chart games not named at that place
    out = []
    for k in range(1, places + 1):
        pp = place_probs[k]
        named = set(pp)
        unnamed_mass = max(0.15, 1.0 - sum(pp.values()))
        others = [u for u in ranks if u not in named]
        if others:
            share = unnamed_mass / len(others)
            for u in others:
                pp[u] += share
        s = sum(pp.values())
        if s <= 0: continue
        inv = 1.0 / s
        for u, p in pp.items():
            out.append({"universe_id": u, "place": k, "p": round(p * inv, 6)})
    return out

def main():
    with open(os.path.join(INPUT_DIR, "task.json")) as f:
        task = json.load(f)
    places = task.get("places", PLACES_DEFAULT)
    with open(os.path.join(INPUT_DIR, "history.ndjson")) as f:
        snaps = [json.loads(l) for l in f if l.strip() and json.loads(l).get("ok", True)]
    snaps.sort(key=lambda s: s["at"])
    probs = forecast(snaps, places)
    # top10 guess = argmax per place
    byplace = collections.defaultdict(list)
    for e in probs:
        byplace[e["place"]].append(e)
    top10 = []
    for k in range(1, places + 1):
        rows = sorted(byplace[k], key=lambda e: -e["p"])
        if rows: top10.append(rows[0]["universe_id"])
    fc = {"schema": "makefun/roblox-up-and-coming-forecast/v1",
          "competition": task.get("competition", "roblox-up-and-coming-forecast-01"),
          "probabilities": probs, "top10": top10}
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, task.get("output", "forecast.json")), "w") as f:
        json.dump(fc, f, indent=1)

if __name__ == "__main__":
    main()
