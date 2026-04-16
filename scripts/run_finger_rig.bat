@echo off
echo ============================================
echo   Blender Finger Rig Auto Generator
echo ============================================
echo.

set BLENDER_PATH=E:\jainmo\blender.exe

if not exist "%BLENDER_PATH%" (
    echo Error: Blender not found - %BLENDER_PATH%
    pause
    exit /b 1
)

echo Using Blender: %BLENDER_PATH%
echo.

set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%smart_finger_rig.py

echo Running script: %PYTHON_SCRIPT%
echo Input file: d641c0d695baef34532beb9539643e3f.fbx
echo.

"%BLENDER_PATH%" --background --python "%PYTHON_SCRIPT%"

echo.
echo ============================================
echo   Done!
echo   Output: d641c0d695baef34532beb9539643e3f_rigged.fbx
echo ============================================
pause
