@echo off

echo For more details please check honorata.log and honorata.err.log

echo New Session >> "%~dp0\honorata.log"
echo New Session >> "%~dp0\honorata.err.log"

set /p DEVICE=<"%~dp0\device.ini"

IF [%DEVICE] == [] GOTO empty

"%~dp0\honorata.exe" startpipe -d %DEVICE% >> "%~dp0\honorata.log" 2>> "%~dp0\honorata.err.log"

:empty

echo Please run getdevice.exe
