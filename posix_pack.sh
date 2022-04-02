#!/bin/bash

VERSION='1.1.0'

if [[ $OSTYPE == "darwin"* ]]; then
    OS="macOS"
    SED_OPT="-s /^dist/discodos/"
    BUILD_DIR=build_app
    DIST_DIR=dist_app
else
    OS="Linux" # FIXME check for family (eg ubuntu 18 alike)
    SED_OPT="--transform s/^dist/discodos/"
    BUILD_DIR=build
    DIST_DIR=dist
fi

# clean up or not
if [[ $1 == '--clean-all' ]]; then
    rm -rf discodos-${VERSION}-${OS}.dmg
    rm -rf $BUILD_DIR
    rm -rf $DIST_DIR
    rm -rf ~/.venvs/discodos_posix_pack
elif [[ $1 == '--clean' ]]; then
    rm -rf discodos-${VERSION}-${OS}.dmg
    rm -rf $BUILD_DIR
    rm -rf $DIST_DIR
fi
# create fresh venv and install deps
# if unclean, existing venv is used
python3 -m venv ~/.venvs/discodos_posix_pack
source ~/.venvs/discodos_posix_pack/bin/activate
pip install --upgrade pip
pip install -r requirements.txt


if [[ $OSTYPE == "darwin"* ]]; then
    # Packaging macOS-app
    # install macOS specific deps
    pip install py2app
    pip install applescript
    # build discodos.app (terminal launch wrapper)
    python setup_macapp.py py2app --bdist-base $BUILD_DIR --dist-dir $DIST_DIR \
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
      "DiscoDOS-${VERSION}-${OS}.dmg" \
      "dist_app/"
else
    # Packaging other posix OS's - Linux, BSD, etc.
    # build bundles
    pyinstaller discodos/cmd/cli.py \
      --onefile \
      --name disco \
      --clean -y -p ~/.venvs/discodos_posix_pack/lib/python3.7/site-packages/ \
      -p ~/.venvs/discodos_pack/src/discogs-client/
    pyinstaller discodos/cmd/sync.py \
      --onefile \
      --name discosync \
      --clean -y -p ~/.venvs/discodos_posix_pack/lib/python3.7/site-packages/ \
      -p ~/.venvs/discodos_pack/src/discogs-client/
    # archive
    tar -zcvf \
      DiscoDOS-${VERSION}-${OS}.tar.gz \
      ${SED_OPT} \
      $DIST_DIR/disco $DIST_DIR/discosync dist/config.yaml
fi

