#!/usr/bin/env sh
set -eu

script="${ECOFLOW_SCRIPT:-ecoflow_cells_csv_dualExtentionBattery.py}"

case "$script" in
  ecoflow_cells_csv.py|ecoflow_cells_csv_dualExtentionBattery.py) ;;
  *)
    echo "Unsupported ECOFLOW_SCRIPT: $script" >&2
    echo "Allowed: ecoflow_cells_csv.py, ecoflow_cells_csv_dualExtentionBattery.py" >&2
    exit 2
    ;;
esac

# ECOFLOW_ARGS is optional and can contain additional CLI args, e.g.:
#   --interval 5 --minutes 30 --master-output /data/master.csv
if [ -n "${ECOFLOW_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  exec python -u "/app/$script" $ECOFLOW_ARGS
else
  exec python -u "/app/$script"
fi
