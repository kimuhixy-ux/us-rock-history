#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== [1/4] backfill_release_group_ids.py ==="
python3 backfill_release_group_ids.py --mode full

echo "=== [2/4] fetch_artwork.py ==="
python3 fetch_artwork.py --mode full

echo "=== [3/4] fetch_personnel.py ==="
python3 fetch_personnel.py --mode full

echo "=== [4/4] fetch_band_lineup.py ==="
python3 fetch_band_lineup.py --mode full

echo "=== PIPELINE COMPLETE ==="
