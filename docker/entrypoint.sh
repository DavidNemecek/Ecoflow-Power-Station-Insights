#!/usr/bin/env sh
set -eu

script="${ECOFLOW_SCRIPT:-ecoflow_cells_csv_dualExtentionBattery.py}"

# Allow passing either:
# - ecoflow_cells_csv.py (basename)
# - collector/ecoflow_cells_csv.py (repo-relative)
case "$script" in
  */*) script_basename="$(basename "$script")" ;;
  *) script_basename="$script" ;;
esac

case "$script_basename" in
  ecoflow_cells_csv.py|ecoflow_cells_csv_dualExtentionBattery.py) ;;
  *)
    echo "Unsupported ECOFLOW_SCRIPT: $script" >&2
    echo "Allowed: ecoflow_cells_csv.py, ecoflow_cells_csv_dualExtentionBattery.py" >&2
    exit 2
    ;;
esac

script_path="/app/collector/$script_basename"
if [ ! -f "$script_path" ]; then
  echo "Script not found: $script_path" >&2
  exit 2
fi

# ECOFLOW_ARGS is optional and can contain additional CLI args, e.g.:
#   --interval 5 --minutes 30 --master-output /data/master.csv
if [ -n "${ECOFLOW_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  exec python -u "$script_path" $ECOFLOW_ARGS
else
  exec python -u "$script_path"
fi
