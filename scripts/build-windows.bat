@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================================
REM  Thorpe — Windows one-click build script
REM  Produces .exe (NSIS) and .msi installers in src-tauri\target\release\bundle\
REM
REM  Prerequisites (install once):
REM    - Node.js 18+     https://nodejs.org/
REM    - Rust (stable)   https://rustup.rs/   then: rustup default stable
REM    - Python 3        https://www.python.org/  (for icon generation)
REM    - Visual Studio Build Tools with "Desktop development with C++"
REM      https://visualstudio.microsoft.com/visual-cpp-build-tools/
REM    - WebView2 Runtime (usually pre-installed on Windows 10/11)
REM ============================================================================

title Thorpe Windows Build

REM Resolve repo root (parent of scripts\)
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
pushd "%ROOT_DIR%" || (
    echo [ERROR] Could not locate project root.
    exit /b 1
)

echo.
echo ============================================================
echo   Thorpe Windows Build
echo ============================================================
echo   Project: %CD%
echo ============================================================
echo.

call :check_prerequisites || exit /b 1
call :generate_icons || exit /b 1
call :install_dependencies || exit /b 1
call :build_frontend || exit /b 1
call :build_tauri || exit /b 1

set "BUNDLE_DIR=%CD%\src-tauri\target\release\bundle"
echo.
echo ============================================================
echo   BUILD SUCCESSFUL
echo ============================================================
echo.
echo Installers should be in:
echo   %BUNDLE_DIR%
echo.
echo Look for:
echo   nsis\   - Windows .exe setup
echo   msi\    - Windows .msi installer
echo.

if exist "%BUNDLE_DIR%" (
    echo Opening bundle folder...
    start "" "%BUNDLE_DIR%"
)

popd
echo.
echo Done. Press any key to close.
pause >nul
exit /b 0

REM ---------------------------------------------------------------------------
:check_prerequisites
echo [1/5] Checking prerequisites...

where node >nul 2>&1 || (
    echo [ERROR] Node.js not found. Install from https://nodejs.org/
    exit /b 1
)
for /f "tokens=*" %%v in ('node -v') do echo        Node.js %%v

where npm >nul 2>&1 || (
    echo [ERROR] npm not found. Reinstall Node.js from https://nodejs.org/
    exit /b 1
)
for /f "tokens=*" %%v in ('npm -v') do echo        npm %%v

where rustc >nul 2>&1 || (
    echo [ERROR] Rust not found. Install from https://rustup.rs/
    echo        After install, open a NEW terminal and run: rustup default stable
    exit /b 1
)
for /f "tokens=*" %%v in ('rustc --version') do echo        %%v

where cargo >nul 2>&1 || (
    echo [ERROR] Cargo not found. Install Rust from https://rustup.rs/
    exit /b 1
)
for /f "tokens=*" %%v in ('cargo --version') do echo        %%v

REM Warn if MSVC linker may be missing (needed for Rust on Windows)
where cl >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] Microsoft C++ compiler ^(cl.exe^) not found in PATH.
    echo           If the Rust build fails, install Visual Studio Build Tools:
    echo           https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo           Select workload: "Desktop development with C++"
    echo           Then restart this script from "x64 Native Tools Command Prompt"
    echo           or a new Command Prompt after installation.
    echo.
) else (
    echo        MSVC cl.exe found
)

exit /b 0

REM ---------------------------------------------------------------------------
:generate_icons
echo.
echo [2/5] Generating app icons...

set "PYTHON_CMD="
where python >nul 2>&1 && set "PYTHON_CMD=python"
if not defined PYTHON_CMD (
    where py >nul 2>&1 && set "PYTHON_CMD=py -3"
)

if defined PYTHON_CMD (
    %PYTHON_CMD% "%SCRIPT_DIR%generate-icons.py"
    if errorlevel 1 (
        echo [ERROR] Icon generation failed.
        exit /b 1
    )
) else (
    echo [WARNING] Python not found — skipping icon generation.
    echo           Install Python 3 or ensure src-tauri\icons\ already exists.
    if not exist "src-tauri\icons\32x32.png" (
        echo [ERROR] No icons found. Install Python and re-run this script.
        exit /b 1
    )
)

REM After npm is available later, tauri icon can refine icons from SVG (optional)
exit /b 0

REM ---------------------------------------------------------------------------
:install_dependencies
echo.
echo [3/5] Installing npm dependencies...
echo        This may take a few minutes on first run...

call npm install
if errorlevel 1 (
    echo [ERROR] npm install failed.
    exit /b 1
)

REM Regenerate proper .ico/.icns from SVG if Tauri CLI is available
if exist "public\thorpe-icon.svg" (
    echo        Refining icons from SVG via Tauri CLI...
    call npx tauri icon "public\thorpe-icon.svg" 2>nul
)

exit /b 0

REM ---------------------------------------------------------------------------
:build_frontend
echo.
echo [4/5] Building React frontend...

call npm run build
if errorlevel 1 (
    echo [ERROR] Frontend build failed.
    exit /b 1
)

exit /b 0

REM ---------------------------------------------------------------------------
:build_tauri
echo.
echo [5/5] Building Thorpe desktop app and Windows installers...
echo        First Rust build can take 10-20+ minutes. Please wait...

call npm run tauri:build
if errorlevel 1 (
    echo.
    echo [ERROR] Tauri build failed.
    echo.
    echo Common fixes:
    echo   - Install Visual Studio Build Tools ^(Desktop development with C++^)
    echo   - Run: rustup update stable
    echo   - Install WebView2: https://developer.microsoft.com/microsoft-edge/webview2/
    echo   - Open "x64 Native Tools Command Prompt for VS" and run this script again
    echo.
    exit /b 1
)

exit /b 0
