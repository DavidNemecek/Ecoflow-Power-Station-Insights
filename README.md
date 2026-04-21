# Ecoflow Power Station Insights

Collect and visualize per-cell voltage data from an **EcoFlow Delta Pro** (and attached Extra Batteries) via the EcoFlow developer API.

## Why this exists (result)

This project was created to identify the cell behavior of an **EcoFlow Delta Pro** over time. In my case, the result was that it was **not a balancing problem**, but a **defective cell in the main battery**.

## Scripts

- [`ecoflow_cells_csv.py`](ecoflow_cells_csv.py): For a Delta Pro with **one** Extra Battery attached on **Port 1** (`SLAVE_BMS_PORT=1`). This setup is **known to work** (see the demo CSVs).
- [`ecoflow_cells_csv_dualExtentionBattery.py`](ecoflow_cells_csv_dualExtentionBattery.py): Intended for a Delta Pro with extra batteries attached. It **should work with any number of extra batteries attached to the main unit**, but this is **not fully tested**.

## Demo CSVs

- Good battery example: `demo/cell_voltages_slave_port1_charge.csv`
- Defective-cell example (main battery): `demo/cell_voltages_master_charge.csv`

## Quickstart

1. Install dependencies:
   - `pip install requests python-dotenv`
2. Create your `.env` (copy and fill in):
   - `copy example.env .env`
3. Run a collector:
   - `python ecoflow_cells_csv.py`
   - `python ecoflow_cells_csv_dualExtentionBattery.py`
4. Visualize the CSV:
   - Open `gui/GUI.html` (or `gui/index.html`) in your browser and load the generated `.csv` file(s).

## Docker

- Create `.env` from `example.env`, then run: `docker compose up --build`
- Default script is `ecoflow_cells_csv_dualExtentionBattery.py`. Switch via `ECOFLOW_SCRIPT=ecoflow_cells_csv.py`.

## Where to get the API keys

- Create an account: <https://developer-eu.ecoflow.com/us>
- Create keys: <https://developer-eu.ecoflow.com/us/security>
- Find the serial number in the EcoFlow app:
  - Battery -> Settings -> Specifications -> Serial Number (often also on the device label).
