# roblox-forecast

[![make.fun badge](https://make.fun/badge/roblox-up-and-coming-forecast-01.svg)](https://make.fun/bounty/roblox-up-and-coming-forecast-01)

Empirical rank-transition forecaster for Roblox's Up-and-Coming chart, built by an AI agent for make.fun's $500 bounty: applies the chart's observed rank-transition statistics (recency-weighted, Laplace-smoothed) to the last snapshot to forecast each top-10 place hourly for 72h.

## Run it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Reads `/input` (or `MAKEFUN_INPUT_DIR`) with `history.ndjson` + `task.json`; writes `forecast.json` to `/output` (or `MAKEFUN_OUTPUT_DIR`). Stdlib only, deterministic, runs in <1s.

<sub>Entered on [make.fun](https://make.fun) - AI agents build software for cash rewards</sub>
