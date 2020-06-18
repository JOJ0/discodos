@echo on
rem echo Activating Python venv
rem start /B "%HOMEPATH%/python-envs/discodos_pack/Scripts/activate.bat"

set VERSION="1.0~rc2"

if "%1"=="clean" (
    del /q dist\discodos
    rmdir dist\discodos
    del /q dist
)

echo Packaging...
pyinstaller discodos\cmd\cli.py --name disco --onefile --clean -y
pyinstaller discodos\cmd\sync.py --name discosync --onefile --clean -y

echo Running _once_ to create config.yaml...
dist\disco.exe

echo Copying to discodos dir...
cd dist
md discodos
copy /y disco.exe discodos
copy /y discosync.exe discodos
copy /y config.yaml discodos

echo Zipping...
set ZIPNAME=discodos-%VERSION%-Win.zip
zip -r %ZIPNAME% discodos
cd ..
move dist\%ZIPNAME% .

