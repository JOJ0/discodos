#!/bin/bash

#set -x
VERS=$1
DRY="echo"

if [ -z $1 ]; then
    echo "Usage: ./bump.sh <version> [doit]"
    exit 0
fi

if [[ "$2" == "doit" ]]; then
    DRY=""
else
    echo -e "\nTHIS IS A DRY-RUN\n"
fi

$DRY git tag -d v$VERS
$DRY git push origin --delete v$VERS
$DRY bump2version build --new-version $VERS --commit --tag --verbose
