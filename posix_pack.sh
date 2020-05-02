#!/bin/bash

VERSION='1.0-rc1'

if [[ $OSTYPE == "darwin"* ]]; then
    OS="macOS"
    SED_OPT="-s /^dist/discodos/"
else
    OS="Linux" # FIXME check for family (eg ubuntu 18 alike)
    SED_OPT="--transform s/^dist/discodos/"
fi

source ~/.venvs/discodos_pack/bin/activate

if [[ $1 == '--clean' ]]; then
    rm -rf dist
fi

pyinstaller cli.py --onefile --name cli --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/

pyinstaller setup.py --onefile --name setup --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/

pyinstaller sync.py --onefile --name sync --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/

tar -zcvf discodos-${VERSION}-${OS}.tar.gz ${SED_OPT} dist/cli dist/setup dist/sync
