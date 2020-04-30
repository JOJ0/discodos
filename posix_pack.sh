#!/bin/bash

VERSION='1.0-rc0'

if [[ $OSTYPE == "darwin"* ]]; then
    OS="MacOSX"
else
    OS="Linux" # FIXME check for family (eg ubuntu 18 alike)
fi

source ~/.venvs/discodos_pack/bin/activate

pyinstaller cli.py --onefile --name cli --distpath discodos --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/

pyinstaller setup.py --onefile --name setup --distpath discodos --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/

pyinstaller sync.py --onefile --name sync --distpath discodos --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/

tar -zcvf discodos-${VERSION}-${OS}.tar.gz discodos
