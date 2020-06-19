@echo on
echo Activating Python venv
rem start /B "%HOMEPATH%\python-envs\discodos_pack\Scripts\activate.bat"
call "%HOMEPATH%"\python-envs\discodos_fresh\Scripts\activate.bat

set VERSION="1.0_rc2"

if "%1"=="clean" (
    del /q dist\discodos
    rmdir dist\discodos
    del /q dist
)

echo Packaging disco...
pyinstaller discodos\cmd\cli.py --name disco --onefile --clean -y --hiddenimport wcwidth --hiddenimport PyYAML -p "%HOMEPATH%"\python-envs\discodos_fresh\Lib\site-packages\ -p  "%HOMEPATH%"\python-envs\discodos_fresh\src\python3-discogs-client\
echo Packaging discosync...
pyinstaller discodos\cmd\sync.py --name discosync --onefile --clean -y -p "%HOMEPATH%"\python-envs\discodos_fresh\Lib\site-packages\

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
"%homepath%"\bin\zip -r %ZIPNAME% discodos
cd ..
move dist\%ZIPNAME% .

