#!/bin/bash
# Script to run the embedding worker as a background process
# Usage: ./run_embedding_worker.sh [batch_size] [interval]

cd "$(dirname "$0")"

BATCH_SIZE=${1:-100}
INTERVAL=${2:-5}

echo "Starting embedding worker with batch_size=$BATCH_SIZE, interval=${INTERVAL}s"

# Run continuously
python -m backend.scripts.embedding_worker --batch-size "$BATCH_SIZE" --interval "$INTERVAL"
