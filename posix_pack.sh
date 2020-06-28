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


if [[ $OSTYPE == "darwin"* ]]; then
    # run _once_ to create install_wrappers_to_cli.sh
    #dist/disco

    # clean up or not
    if [[ $1 == '--clean' ]]; then
        rm -rf build_app
        rm -rf dist_app
    fi
    # check if py2app installed in current env
    pip show -q py2app
    PY2APP_INSTALLED=$(echo $?)
    if [[ PY2APP_INSTALLED -ne 0 ]]; then
        pip install py2app
    fi
    # build discodos.app (terminal launch wrapper)
    python setup_macapp.py py2app --bdist-base build_app --dist-dir dist_app --extra-scripts discodos/cmd/cli.py,discodos/cmd/sync.py
    # run _once_ to create install_wrappers_to_cli.sh
    #dist_app/discodos.app/Contents/MacOS/cli

    #tar -zcvf discodos-${VERSION}-${OS}.tar.gz ${SED_OPT} dist/disco dist/discosync dist/config.yaml
else
    if [[ $1 == '--clean' ]]; then
        rm -rf build
        rm -rf dist
    fi
    # build bundles
    pyinstaller discodos/cmd/cli.py --onefile --name disco --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/
    pyinstaller discodos/cmd/sync.py --onefile --name discosync --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/
    # run _once_ to create config.yaml
    dist/disco

    tar -zcvf discodos-${VERSION}-${OS}.tar.gz ${SED_OPT} dist/disco dist/discosync dist/config.yaml
fi



