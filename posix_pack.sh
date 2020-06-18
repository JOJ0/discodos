#!/bin/bash

VERSION='1.0_rc2'

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

pyinstaller discodos/cmd/cli.py --onefile --name disco --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/

pyinstaller discodos/cmd/sync.py --onefile --name discosync --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/

# run _once_ to create config.yaml
dist/disco

tar -zcvf discodos-${VERSION}-${OS}.tar.gz ${SED_OPT} dist/disco dist/discosync dist/config.yaml
