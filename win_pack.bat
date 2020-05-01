@echo on
rem echo Activating Python venv
rem start /B "%HOMEPATH%/python-envs/discodos_pack/Scripts/activate.bat"

echo Packaging...
pyinstaller cli.py --onefile --clean -y
pyinstaller setup.py --name winconfig --onefile --clean -y
pyinstaller sync.py --onefile --clean -y

echo Copying to discodos dir...
cd dist
md discodos
copy /y cli.exe discodos
copy /y winconfig.exe discodos
copy /y sync.exe discodos

echo Zipping....
zip -r discodos.zip discodos
cd ..
move dist\discodos.zip .

