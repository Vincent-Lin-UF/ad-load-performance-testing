#!/usr/bin/env bash
TARGET=boxing
RUNS=4

for i in $(seq 1 $RUNS); do
  ad-load run "$TARGET" --bare
  mv prebid_summaries.json    "${TARGET}_run_${i}_prebid_summaries.json"
  mv google_ads_summary.json  "${TARGET}_run_${i}_google_ads_summary.json"
  mv performance_metrics.json "${TARGET}_run_${i}_performance_metrics.json"
done

echo "All done."