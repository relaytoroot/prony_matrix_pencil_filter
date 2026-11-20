@echo off
setlocal
pushd "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Die Python-Umgebung fehlt. Bitte zuerst die Installation in der README ausfuehren.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m prony_filter.labor
if errorlevel 1 pause
popd
