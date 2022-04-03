#!/bin/bash
# Upgrade dependencies in pynsist.cfg, then run
python -m nsist pynsist.cfg
echo "Build successful? Make sure file is named DiscoDOS-<version>-Win.exe (dashes!) and upload to github relase."
