#!/bin/bash

VERSION='1.0_rc3'

if [[ $OSTYPE == "darwin"* ]]; then
    OS="macOS"
    SED_OPT="-s /^dist/discodos/"
else
    OS="Linux" # FIXME check for family (eg ubuntu 18 alike)
    SED_OPT="--transform s/^dist/discodos/"
fi

source ~/.venvs/discodos_pack/bin/activate


if [[ $OSTYPE == "darwin"* ]]; then
    # Packaging macOS-app
    # clean up or not
    if [[ $1 == '--clean' ]]; then
        rm -rf discodos-${VERSION}-${OS}.dmg
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
    python setup_macapp.py py2app --bdist-base build_app --dist-dir dist_app \
      --packages dropbox \
      --extra-scripts discodos/cmd/cli.py,discodos/cmd/sync.py
      #--debug-modulegraph \

    create-dmg \
      --volname "DiscoDOS-${VERSION}" \
      --volicon "assets/discodos_7-v6_big_fat_D.icns" \
      --background "assets/discodos_logo_v0.3_solarized_1033x625.png" \
      --window-pos 200 120 \
      --window-size 850 500 \
      --icon-size 100 \
      --icon "DiscoDOS.app" 145 170 \
      --hide-extension "DiscoDOS.app" \
      --app-drop-link 600 65 \
      "discodos-${VERSION}-${OS}.dmg" \
      "dist_app/"
else
    # Packaging other posix OS's - Linux, BSD, etc.
    # clean up or not
    if [[ $1 == '--clean' ]]; then
        rm -rf discodos-${VERSION}-${OS}.tar.gz
        rm -rf build
        rm -rf dist
    fi
    # build bundles
    pyinstaller discodos/cmd/cli.py --onefile --name disco --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/
    pyinstaller discodos/cmd/sync.py --onefile --name discosync --clean -y -p ~/.venvs/discodos_pack/lib/python3.7/site-packages/ -p ~/.venvs/discodos_pack/src/discogs-client/
    # archive
    tar -zcvf discodos-${VERSION}-${OS}.tar.gz ${SED_OPT} dist/disco dist/discosync dist/config.yaml
fi



