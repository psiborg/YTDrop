@echo off
setlocal EnableDelayedExpansion

title YTDrop Launcher

echo.
echo  ================================
echo    YTDrop - yt-dlp GUI Launcher
echo  ================================
echo.

:: -- Check Python --------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not found on PATH.
    echo.
    echo  Please install Python 3.8+ from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] Python %PY_VER% found.

:: -- Check yt-dlp --------------------------------------------------------------
where yt-dlp >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] yt-dlp.exe not found on PATH.
    echo.
    echo  Download the standalone binary from:
    echo    https://github.com/yt-dlp/yt-dlp/releases/latest
    echo.
    echo  Place yt-dlp.exe in the same folder as ytdrop.py,
    echo  or in any folder that is already on your PATH.
    echo.
    pause
    exit /b 1
)
echo  [OK] yt-dlp found.

:: -- Check tkinter -------------------------------------------------------------
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] tkinter is not available.
    echo  Please reinstall Python and ensure the "tcl/tk" option is selected.
    pause
    exit /b 1
)
echo  [OK] tkinter found.

:: -- Check ffmpeg (optional) ---------------------------------------------------
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo  [WARN] ffmpeg not found on PATH. Audio extraction and video merging may fail.
    echo         Download from https://ffmpeg.org/download.html and add to PATH.
) else (
    echo  [OK] ffmpeg found.
)

:: -- Locate ytdrop.py ----------------------------------------------------------
set SCRIPT_DIR=%~dp0
set APP=%SCRIPT_DIR%ytdrop.py

if not exist "%APP%" (
    echo.
    echo  [ERROR] ytdrop.py not found in: %SCRIPT_DIR%
    echo  Please ensure launch.bat is in the same folder as ytdrop.py
    pause
    exit /b 1
)

:: -- Launch --------------------------------------------------------------------
echo.
echo  Launching YTDrop...
echo.
start "" pythonw "%APP%"

endlocal
