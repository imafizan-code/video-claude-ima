#!/bin/sh
# Regenerate the composition, then (re)apply the sun-kissed grade to the talking-head media.
set -e
cd "$(dirname "$0")/.."
HF=${HF:-npx --yes hyperframes@0.8.197}
python3 build/gen.py
GRADE='{"preset":"warm-daylight","intensity":0.6,"adjust":{"exposure":-0.05,"contrast":0.06,"temperature":0.13,"tint":0.02,"highlights":-0.2,"whites":-0.08,"shadows":0.06,"vibrance":0.05},"effects":{"bloom":0.12,"bloomRadius":10}}'
$HF media-treatment --selector "#facewrap video" --grading "$GRADE" --apply --json >/dev/null
$HF media-treatment --selector "#v-hold" --grading "$GRADE" --apply --json >/dev/null
echo "composition + grade ready"
