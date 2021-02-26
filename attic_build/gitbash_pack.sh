#!/bin/bash
# package for windows running git-bash
echo Activating Python venv
. "$HOME/python-envs/discodos_fresh/Scripts/activate"


VERSION='1.0_rc2'

if [[ $1 == '--clean' ]]; then
    rm -rf dist
fi

echo Packaging disco...
pyinstaller discodos/cmd/cli.py --name disco --onefile --clean -y -p ~/python-envs/discodos_fresh/Lib/site-packages/ -p  ~/python-envs/discodos_fresh/src/python3-discogs-client/
echo Packaging discosync...
pyinstaller discodos/cmd/sync.py --name discosync --onefile --clean -y -p ~/python-envs/discodos_fresh/Lib/site-packages/ -p  ~/python-envs/discodos_fresh/src/python3-discogs-client/

echo Running _once_ to create config.yaml...
dist/disco.exe

echo Copying to discodos dir...
cd dist
mkdir discodos
cp disco.exe discodos
cp discosync.exe discodos
cp config.yaml discodos

echo Zipping...
ZIPNAME=discodos-${VERSION}-Win.zip
$HOME/bin/zip -r $ZIPNAME discodos

cd ..
mv dist/${ZIPNAME} .

