#!/bin/bash

VERSION='1.0-rc0'

if [[ $OSTYPE == "darwin"* ]]; then
    OS="MacOSX"
else
    OS="Linux" # FIXME check for family (eg ubuntu 18 alike)
fi

source ~/.venvs/discodos_pack/bin/activate

pyinstaller cli.py --onefile --name cli --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/

pyinstaller setup.py --onefile --name setup --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/

pyinstaller sync.py --onefile --name sync --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/

if [[ $1 == '--clean' ]]; then
    rm -rf discodos
    mv -v dist discodos
else
    rmdir discodos
    mv dist/* discodos/
fi

tar -zcvf discodos-${VERSION}-${OS}.tar.gz discodos
