#!/bin/bash
# Create a python env and install requirements on Windows 10

ENV="$HOME/python-envs/discodos_fresh"
REQ="$HOME/discodos_fresh/requirements.txt" 

if [[ $1 == '--clean' ]]; then
    echo Deleting environment dir
    rm -rf $ENV
    echo Creating environment
    python -m venv $ENV
    echo Installing pyinstaller globally
    pip install pyinstaller
fi

echo Activating Python venv
. "$ENV/Scripts/activate"


if [ -f $REQ ]; then
    pip install -r "$REQ" 
else
    echo "Requirements file non-existent"
fi
