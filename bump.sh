#!/bin/bash

set -x
VERS=$1

git tag -d v$VERS; git push origin --delete v$VERS; bumpversion build --new-version $VERS --commit --tag --verbose
