# Ecoflow Power Station Insights

Collect and visualize per-cell voltage data from an **EcoFlow Delta Pro** (and attached Extra Batteries) via the EcoFlow developer API.

## Website (viewer)

- Live viewer: <https://davidnemecek.github.io/Ecoflow-Power-Station-Insights/>

## Why this exists (result)

This project was created to identify the cell behavior of an **EcoFlow Delta Pro** over time. In my case, the result was that it was **not a balancing problem**, but a **defective cell in the main battery**.

## Scripts

- [`collector/ecoflow_cells_csv.py`](collector/ecoflow_cells_csv.py): For a Delta Pro with **one** Extra Battery attached on **Port 1** (`SLAVE_BMS_PORT=1`). This setup is **known to work** (see the demo CSVs).
- [`collector/ecoflow_cells_csv_dualExtentionBattery.py`](collector/ecoflow_cells_csv_dualExtentionBattery.py): Intended for a Delta Pro with extra batteries attached. It **should work with any number of extra batteries attached to the main unit**, but this is **not fully tested**.

## Demo CSVs

- Good battery example: `demo/cell_voltages_slave_port1_charge.csv`
- Defective-cell example (main battery): `demo/cell_voltages_master_charge.csv`

## Quickstart

### Option 1: Docker (recommended)

1. Create your `.env` (copy and fill in):
   - `copy example.env .env`
2. Run the collector:
   - `docker compose pull && docker compose up -d`
   - Optional: set `LOG_LEVEL=debug` (or `info`, `warning`, `error`) in your `.env`
   - Optional: set `MINUTES=60` in your `.env` (if omitted, it runs forever and logs a warning)
3. Find the CSVs in `output/` and open them in the viewer:
   - <https://davidnemecek.github.io/Ecoflow-Power-Station-Insights/>
   - or `gui/GUI.html` locally

### Option 2: Run with Python

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Create your `.env` (copy and fill in):
   - `copy example.env .env`
3. Run a collector:
   - `python collector/ecoflow_cells_csv.py --log-level info`
   - `python collector/ecoflow_cells_csv_dualExtentionBattery.py --log-level info`
4. Visualize the CSV:
   - <https://davidnemecek.github.io/Ecoflow-Power-Station-Insights/>
   - or `gui/GUI.html` locally

## Docker

- Create `.env` from `example.env`, then run: `docker compose up --build`
- Default script is `ecoflow_cells_csv_dualExtentionBattery.py`. Switch via `ECOFLOW_SCRIPT=ecoflow_cells_csv.py`.
- Set log verbosity with `LOG_LEVEL=debug|info|warning|error`.
- Set runtime via `MINUTES=60` (if omitted, it runs forever and logs a warning).

## Where to get the API keys

- Create an account: <https://developer-eu.ecoflow.com/us>
- Create keys: <https://developer-eu.ecoflow.com/us/security>
- Find the serial number in the EcoFlow app:
  - Battery -> Settings -> Specifications -> Serial Number (often also on the device label).
