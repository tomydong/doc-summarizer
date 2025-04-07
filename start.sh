#!/bin/bash

# Tính số workers tối ưu dựa trên số CPU
WORKERS=$(( 2 * $(nproc) + 1 ))
echo "Starting with $WORKERS workers"

# Chạy Gunicorn với các tham số tối ưu
exec gunicorn --workers=$WORKERS \
              --threads=2 \
              --worker-class=gthread \
              --bind 0.0.0.0:5000 \
              --timeout=120 \
              --keep-alive=5 \
              --max-requests=1000 \
              --max-requests-jitter=50 \
              app:app