@echo on
"%HOMEPATH%/python-envs/discodos_pack/Scripts/activate.bat"

echo Packaging...
echo
echo
echo
pyinstaller cli.py --onefile --clean -y
pyinstaller setup.py --name winconfig --onefile --clean -y
pyinstaller sync.py --onefile --clean -y
echo
echo
echo
echo
echo
echo

echo Zipping....
echo
echo
echo
zip -r mydir.zip mydir
echo
echo
echo
