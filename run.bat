@echo off
setlocal enabledelayedexpansion

set "COMMAND=%1"

for /f "tokens=1,* delims= " %%a in ("%*") do set "OTHERS=%%b"
for /f "tokens=2 delims= " %%a in ("%*") do set "SUB_ARG=%%a"

if "%COMMAND%"=="server" (
    call :run_server %OTHERS%
) else if "%COMMAND%"=="setup" (
    call :setup_project
) else if "%COMMAND%"=="app" (
    call :run_app %OTHERS%
) else if "%COMMAND%"=="analyze" (
    if "%SUB_ARG%"=="--clean" call :clean_results
    if "%SUB_ARG%"=="--fresh" call :clean_errors
    call :run_analyze %OTHERS%
) else if "%COMMAND%"=="clean" (
    if "%SUB_ARG%"=="--errors" call :clean_errors
    if "%SUB_ARG%"=="--logs" call :clean_logs
    if "%SUB_ARG%"=="--results" call :clean_results
    if "%SUB_ARG%"=="--all" (
        call :clean_logs
        call :clean_results
    )
) else if "%COMMAND%"=="sum" (
    call :count_errors data\results\checkpoint.json
) else (
    echo Unrecognized command: %COMMAND%
)
goto :eof

:run_server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 %*
goto :eof

:run_app
uv run gradio_app/app.py %*
goto :eof

:run_analyze
uv run pipeline_analysis.py %*
goto :eof

:clean_results
if exist data\results\ del /q /s data\results\* >nul 2>&1
if exist data\history\ del /q /s data\history\* >nul 2>&1
goto :eof

:clean_logs
if exist logs\ del /q /s logs\* >nul 2>&1
goto :eof

:clean_errors
uv run utils/clean_errors.py
goto :eof

:count_errors
set "FILE_PATH=%1"

if not exist "%FILE_PATH%" (
    echo [WARN] File not found: %FILE_PATH%
    goto :eof
)

set "JQ_QUERY_1=[.[] | select(.is_failed == true) | .filename]"
set "JQ_QUERY_2=[.[] | select(.is_failed == true)] | length"

for /f "delims=" %%i in ('jq "!JQ_QUERY_1!" "%FILE_PATH%"') do set "FAILED_FILES=%%i"
for /f "delims=" %%i in ('jq "!JQ_QUERY_2!" "%FILE_PATH%"') do set "TOTAL_FAILED=%%i"
for /f "delims=" %%i in ('jq ". | length" "%FILE_PATH%"') do set "TOTAL_DATA=%%i"

for /f "delims=" %%i in ('powershell -Command "[math]::Round(($TOTAL_FAILED / $TOTAL_DATA) * 100, 2)"') do set "FAILED_PERCENT=%%i"
set /a SUCCESS_DATA=%TOTAL_DATA% - %TOTAL_FAILED%

echo [INFO] Failed files: !FAILED_FILES!
echo [INFO] Total 'is_failed: true': !TOTAL_FAILED! of !TOTAL_DATA! ^| ~!SUCCESS_DATA! (!FAILED_PERCENT!%%) (%FILE_PATH%)
goto :eof

:setup_project
if exist pyproject.toml (
    uv venv
    uv sync
    uv pip install -r requirements.txt
) else (
    uv init .
    uv venv
    uv sync
    uv pip install -r requirements.txt
)
goto :eof