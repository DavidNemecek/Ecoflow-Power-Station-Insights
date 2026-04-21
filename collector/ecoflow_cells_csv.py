#!/usr/bin/env python3
import argparse
import csv
import hashlib
import hmac
import json
import logging
import os
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


def setup_logging(level: str) -> logging.Logger:
    level_norm = (level or "info").strip().lower()
    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }
    if level_norm not in levels:
        raise SystemExit("Invalid log level. Use one of: debug, info, warning, error")

    logging.basicConfig(
        level=levels[level_norm],
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return logging.getLogger("ecoflow")


def require_env(name: str, value: str | None) -> str:
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_config() -> tuple[str, str, str, str, str, int]:
    load_dotenv()

    access_key = require_env("ACCESS_KEY", os.getenv("ACCESS_KEY"))
    secret_key = require_env("SECRET_KEY", os.getenv("SECRET_KEY"))
    serial_number = require_env("SERIAL_NUMBER", os.getenv("SERIAL_NUMBER"))
    base_url = os.getenv("BASE_URL", "https://api.ecoflow.com")
    api_path = os.getenv("API_PATH", "/iot-open/sign/device/quota/all")
    slave_bms_port = int(os.getenv("SLAVE_BMS_PORT", "1"))
    return access_key, secret_key, serial_number, base_url, api_path, slave_bms_port


def hmac_sha256_hex(data: str, key: str) -> str:
    return hmac.new(key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()


def build_query_string(params: dict) -> str:
    return "&".join(f"{k}={params[k]}" for k in sorted(params.keys()))


def ecoflow_get(url: str, access_key: str, secret_key: str, params: dict | None = None) -> dict:
    nonce = str(random.randint(100000, 999999))
    timestamp = str(int(time.time() * 1000))

    headers = {
        "accessKey": access_key,
        "nonce": nonce,
        "timestamp": timestamp,
    }

    sign_str = ""
    if params:
        sign_str += build_query_string(params) + "&"
    sign_str += build_query_string(headers)

    headers["sign"] = hmac_sha256_hex(sign_str, secret_key)

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _get_by_path(container: object, path: list[object]) -> object | None:
    if not isinstance(path, list) or not path:
        return None

    if isinstance(container, dict):
        flat_key = ".".join(str(p) for p in path)
        if flat_key in container:
            return container[flat_key]

    current: object = container
    for part in path:
        if isinstance(current, dict):
            if part in current:
                current = current[part]
                continue
            part_str = str(part)
            if part_str in current:
                current = current[part_str]
                continue
            if part_str.isdigit():
                part_int = int(part_str)
                if part_int in current:
                    current = current[part_int]
                    continue
            return None
        if isinstance(current, list):
            if isinstance(part, int):
                idx = part
            else:
                part_str = str(part)
                if not part_str.isdigit():
                    return None
                idx = int(part_str)
            if idx < 0 or idx >= len(current):
                return None
            current = current[idx]
            continue
        return None

    return current


def _normalize_cell_voltages(cell_voltages: object) -> list[int]:
    if not isinstance(cell_voltages, list):
        raise TypeError(f"Unexpected cellVol type: {type(cell_voltages).__name__}")
    return [int(v) for v in cell_voltages]


def _candidate_slave_base_paths(port: int) -> list[list[object]]:
    return [
        ["bmsSlave", str(port)],
        ["bmsSlave", port],
        ["bmsSlave", port - 1],
        [f"bmsSlave{port}"],
        [f"bmsSlave_{port}"],
        [f"bmsSlavePort{port}"],
        [f"bmsSlavePort_{port}"],
        ["bmsSlave"],
    ]


def extract_cell_voltages(payload: dict, *, bms: str = "master", slave_port: int = 1) -> tuple[list[int], dict]:
    data = payload.get("data", payload)

    if bms == "master":
        base_paths = [["bmsMaster"]]
    elif bms == "slave":
        base_paths = _candidate_slave_base_paths(slave_port)
    else:
        raise ValueError("bms must be 'master' or 'slave'")

    for base in base_paths:
        cell_voltages = _get_by_path(data, base + ["cellVol"])
        if cell_voltages is None:
            continue

        series_num = _get_by_path(data, base + ["cellSeriesNum"])
        min_cell = _get_by_path(data, base + ["minCellVol"])
        max_cell = _get_by_path(data, base + ["maxCellVol"])

        meta = {
            "series_num": series_num,
            "min_cell_mv": min_cell,
            "max_cell_mv": max_cell,
            "bms": bms,
            "slave_port": slave_port if bms == "slave" else None,
        }
        return _normalize_cell_voltages(cell_voltages), meta

    if isinstance(data, dict):
        likely = sorted(k for k in data.keys() if re.search(r"\bbms(Slave|Master)\b", str(k)) and "cellVol" in str(k))
        if bms == "slave":
            raise KeyError(
                f"Slave BMS cell voltages not found (port {slave_port}). "
                f"Keys containing bms*/cellVol: {likely}"
            )
        raise KeyError(f"Master BMS cell voltages not found. Keys containing bms*/cellVol: {likely}")

    raise KeyError("BMS cell voltages not found; unexpected payload format.")


def _cell_headers_mv(cell_count: int) -> list[str]:
    return [f"cell_{i:02d}_mv" for i in range(1, cell_count + 1)]


def _ensure_wide_csv_header(path: Path, *, cell_count: int) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_utc", *_cell_headers_mv(cell_count)])


def _append_wide_row(path: Path, *, timestamp_utc: str, cells_mv: list[int], expected_cell_count: int) -> None:
    if len(cells_mv) != expected_cell_count:
        raise ValueError(f"{path}: expected {expected_cell_count} cells, got {len(cells_mv)}")
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp_utc, *cells_mv])


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Log EcoFlow BMS cell voltages to CSV (wide rows, master + slave).")
    parser.add_argument(
        "--log-level",
        type=str.lower,
        default=os.getenv("LOG_LEVEL", "info").lower(),
        choices=["debug", "info", "warning", "error"],
        help="Log level (default: env LOG_LEVEL or info)",
    )
    parser.add_argument("--master-output", default="cell_voltages_master.csv", help="Master CSV path")
    parser.add_argument("--slave-output", default=None, help="Slave CSV path (default: cell_voltages_slave_portN.csv)")
    parser.add_argument("--interval", type=float, default=10.0, help="Polling interval seconds (default: 10)")
    parser.add_argument("--minutes", type=float, default=None, help="Total runtime in minutes (default: run forever)")
    parser.add_argument("--slave-port", type=int, default=None, help="Slave BMS port (default: env SLAVE_BMS_PORT or 1)")
    args = parser.parse_args()

    logger = setup_logging(args.log_level)
    access_key, secret_key, serial_number, base_url, api_path, default_slave_port = load_config()
    slave_port = args.slave_port if args.slave_port is not None else default_slave_port

    url = f"{base_url}{api_path}"
    master_path = Path(args.master_output)
    slave_path = Path(args.slave_output) if args.slave_output else Path(f"cell_voltages_slave_port{slave_port}.csv")

    if args.minutes is not None and args.minutes <= 0:
        raise SystemExit("--minutes must be > 0 (or omit it to run forever)")

    sample = 0
    master_cell_count: int | None = None
    slave_cell_count: int | None = None
    stop_at: float | None = None
    if args.minutes is not None:
        stop_at = time.monotonic() + (args.minutes * 60.0)

    slave_present: bool | None = None
    try:
        while True:
            if stop_at is not None and time.monotonic() >= stop_at:
                return 0

            sample += 1
            payload = ecoflow_get(url, access_key, secret_key, {"sn": serial_number})

            if str(payload.get("code")) not in ("0", "200", "None", "null") and payload.get("data") is None:
                raise RuntimeError(f"Unexpected API response: {json.dumps(payload, ensure_ascii=False)}")

            ts = datetime.now(timezone.utc).isoformat()

            master_cells, master_meta = extract_cell_voltages(payload, bms="master")
            if master_cell_count is None:
                master_cell_count = len(master_cells)
                _ensure_wide_csv_header(master_path, cell_count=master_cell_count)
            _append_wide_row(master_path, timestamp_utc=ts, cells_mv=master_cells, expected_cell_count=master_cell_count)

            try:
                slave_cells, slave_meta = extract_cell_voltages(payload, bms="slave", slave_port=slave_port)
            except KeyError as e:
                if slave_present is not False:
                    logger.info("Slave BMS (port %s) not detected; pausing logging", slave_port)
                    logger.debug("Slave BMS missing detail: %s", e)
                slave_present = False
                time.sleep(max(args.interval, 0.1))
                continue

            if slave_present is not True:
                logger.info("Slave BMS (port %s) detected; resuming logging to %s", slave_port, slave_path)
            slave_present = True

            if slave_cell_count is None:
                slave_cell_count = len(slave_cells)
                _ensure_wide_csv_header(slave_path, cell_count=slave_cell_count)
            _append_wide_row(slave_path, timestamp_utc=ts, cells_mv=slave_cells, expected_cell_count=slave_cell_count)

            time.sleep(max(args.interval, 0.1))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
