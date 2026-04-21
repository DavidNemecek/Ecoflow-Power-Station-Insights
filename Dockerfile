FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ECOFLOW_SCRIPT=ecoflow_cells_csv_dualExtentionBattery.py \
    ECOFLOW_ARGS=""

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY collector /app/collector
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Default output location for generated CSV files (mount a volume here).
WORKDIR /data

ENTRYPOINT ["/entrypoint.sh"]
