@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title ⚙️ DowFlow DEBUG CENTER — Professional Toolkit
cd /d "%~dp0"

REM ═══════════════════════════════════════════════════════════════════
REM  DOWFLOW DEBUG CENTER — Version Pro
REM  Menu interactif + diagnostics complets + logs persistants
REM ═══════════════════════════════════════════════════════════════════

set "LOG_DIR=%~dp0logs"
set "STAMP=%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
set "STAMP=%STAMP: =0%"
set "LOG_FILE=%LOG_DIR%\debug_%STAMP%.log"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "SEPARATOR=═══════════════════════════════════════════════════════════════"
set "OK=[ ✓  OK  ]"
set "WARN=[ ⚠ WARN ]"
set "FAIL=[ ✗ FAIL ]"
set "INFO=[ ℹ INFO ]"

REM ── COLORS (ANSI escape codes ─────────────────────────────────────
set "C_RST=\033[0m"
set "C_RED=\033[91m"
set "C_GRN=\033[92m"
set "C_YEL=\033[93m"
set "C_BLU=\033[94m"
set "C_CYN=\033[96m"
set "C_WHT=\033[97m"
set "C_BOLD=\033[1m"

REM ═══════════════════════════════════════════════════════════════════
REM  :LOGGER — Écrit dans la console ET le fichier log
REM ═══════════════════════════════════════════════════════════════════
:LOGGER
echo %~1
echo [%TIME%] %~1 >> "%LOG_FILE%"
goto :eof

:LOGGER_NONL
<nul set /p "=%~1"
echo|set /p "=[%TIME%] %~1" >> "%LOG_FILE%"
goto :eof

REM ═══════════════════════════════════════════════════════════════════
REM  :BANNER
REM ═══════════════════════════════════════════════════════════════════
:BANNER
cls
echo.
echo   %C_BOLD%%C_RED%╔══════════════════════════════════════════════════════════════╗%C_RST%
echo   %C_BOLD%%C_RED%║%C_RST%          %C_BOLD%%C_YEL%⚙️  DOWFLOW DEBUG CENTER  ⚙️%C_RST%                      %C_BOLD%%C_RED%║%C_RST%
echo   %C_BOLD%%C_RED%║%C_RST%      %C_CYN%Professional Diagnostic Toolkit v2.0%C_RST%               %C_BOLD%%C_RED%║%C_RST%
echo   %C_BOLD%%C_RED%╚══════════════════════════════════════════════════════════════╝%C_RST%
echo.
echo   %C_CYN%Session log :%C_RST% %LOG_FILE%
echo   %C_CYN%Dossier     :%C_RST% %~dp0
echo   %C_CYN%Date/Heure  :%C_RST% %DATE% %TIME%
echo.
goto :eof

REM ═══════════════════════════════════════════════════════════════════
REM  :MENU_PRINCIPAL
REM ═══════════════════════════════════════════════════════════════════
:MENU_PRINCIPAL
call :BANNER
echo   %C_BOLD%%C_BLU%┌──────────────────────────────────────────────────────────────┐%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%                 %C_BOLD%📋 MENU PRINCIPAL%C_RST                        %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%├──────────────────────────────────────────────────────────────┤%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%  %C_YEL%1%C_RST% - 🔍 Diagnostic COMPLET (tous les checks)              %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%  %C_YEL%2%C_RST% - 🐍 Vérifier Python + Environnement virtuel            %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%  %C_YEL%3%C_RST% - 📦 Vérifier Dépendances (yt-dlp, flask, playwright...)  %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%  %C_YEL%4%C_RST% - 🎬 Vérifier FFmpeg + FFprobe + aria2c                   %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%  %C_YEL%5%C_RST% - 🌐 Vérifier Playwright + Navigateur + Extraction URL  %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%  %C_YEL%6%C_RST% - 🧪 Test de téléchargement YouTube (vidéo test)          %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%  %C_YEL%7%C_RST% - 📡 Test réseau + DNS + Connectivité sites cibles        %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%  %C_YEL%8%C_RST% - 🔧 Imports codebase + healthcheck Flask              %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%  %C_YEL%9%C_RST% - 📂 Ouvrir dossier logs / downloads                     %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%  %C_YEL%A%C_RST% - 🚀 Démarrer DowFlow en mode DEBUG                          %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%│%C_RST%  %C_YEL%0%C_RST% - ❌ Quitter                                              %C_BOLD%%C_BLU%│%C_RST%
echo   %C_BOLD%%C_BLU%└──────────────────────────────────────────────────────────────┘%C_RST%
echo.
set "CHOIX="
set /p "CHOIX=%C_BOLD%%C_YEL%  ➜ Choisis une option : %C_RST%"

if "%CHOIX%"=="1" goto :DIAG_FULL
if "%CHOIX%"=="2" goto :CHECK_PYTHON
if "%CHOIX%"=="3" goto :CHECK_DEPS
if "%CHOIX%"=="4" goto :CHECK_TOOLS
if "%CHOIX%"=="5" goto :CHECK_PLAYWRIGHT
if "%CHOIX%"=="6" goto :TEST_YTDLP
if "%CHOIX%"=="7" goto :TEST_NETWORK
if "%CHOIX%"=="8" goto :CHECK_CODEBASE
if "%CHOIX%"=="9" goto :OPEN_FOLDERS
if /i "%CHOIX%"=="A" goto :START_DEBUG
if /i "%CHOIX%"=="Q" goto :FIN
if "%CHOIX%"=="0" goto :FIN
goto :MENU_PRINCIPAL

REM ═══════════════════════════════════════════════════════════════════
REM  :DIAG_FULL — Tous les checks à la suite
REM ═══════════════════════════════════════════════════════════════════
:DIAG_FULL
call :BANNER
call :LOGGER "═══════════════════════════════════════════════════════════════"
call :LOGGER "🕐 DIAGNOSTIC COMPLET DÉMARRÉ"
call :LOGGER "═══════════════════════════════════════════════════════════════"
echo.
call :CHECK_PYTHON_INTERNAL
call :CHECK_DEPS_INTERNAL
call :CHECK_TOOLS_INTERNAL
call :CHECK_PLAYWRIGHT_INTERNAL
call :CHECK_CODEBASE_INTERNAL
call :TEST_NETWORK_INTERNAL
echo.
call :LOGGER "═══════════════════════════════════════════════════════════════"
call :LOGGER "✅ DIAGNOSTIC COMPLET TERMINÉ"
call :LOGGER "═══════════════════════════════════════════════════════════════"
echo.
echo   %C_GRN%  ► Rapport complet sauvegardé dans :%C_RST%
echo      %LOG_FILE%
echo.
pause
goto :MENU_PRINCIPAL

REM ═══════════════════════════════════════════════════════════════════
REM  :CHECK_PYTHON
REM ═══════════════════════════════════════════════════════════════════
:CHECK_PYTHON
call :BANNER
echo   %C_BOLD%%C_YEL%🐍  VÉRIFICATION PYTHON + VENV%C_RST%
echo   %SEPARATOR%
call :CHECK_PYTHON_INTERNAL
echo.
pause
goto :MENU_PRINCIPAL

:CHECK_PYTHON_INTERNAL
echo.
call :LOGGER_NONL "  Python présent          : "
where python >nul 2>&1
if errorlevel 1 (
    call :LOGGER "%C_RED%%FAIL% Python introuvable dans PATH%C_RST%"
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set "PYV=%%i"
    call :LOGGER "%C_GRN%%OK% !PYV!%C_RST%"
)

call :LOGGER_NONL "  Chemin Python           : "
for /f "delims=" %%i in ('where python 2^>nul') do (
    call :LOGGER "%C_CYN%%%i%C_RST%"
    goto :PY_DONE
)
call :LOGGER "%C_RED%introuvable%C_RST%"
:PY_DONE

call :LOGGER_NONL "  Virtualenv (.venv)      : "
if exist ".venv\Scripts\python.exe" (
    call :LOGGER "%C_GRN%%OK% Existe%C_RST%"
    call :LOGGER_NONL "  Activation venv         : "
    call .venv\Scripts\activate.bat
    call :LOGGER "%C_GRN%%OK% Activé (python=%VIRTUAL_ENV%)%C_RST%"
) else (
    call :LOGGER "%C_YEL%%WARN% Absent — utiliser start.bat pour le créer%C_RST%"
)

call :LOGGER_NONL "  pip disponible          : "
where pip >nul 2>&1
if errorlevel 1 (
    call :LOGGER "%C_RED%%FAIL% pip absent%C_RST%"
) else (
    call :LOGGER "%C_GRN%%OK%%C_RST%"
)

call :LOGGER_NONL "  Dossier downloads/      : "
if exist "downloads" (
    call :LOGGER "%C_GRN%%OK%%C_RST%"
) else (
    call :LOGGER "%C_YEL%%WARN% Absent — création en cours..."
    mkdir downloads
    call :LOGGER "%C_GRN%%OK% Créé%C_RST%"
)
goto :eof

REM ═══════════════════════════════════════════════════════════════════
REM  :CHECK_DEPS
REM ═══════════════════════════════════════════════════════════════════
:CHECK_DEPS
call :BANNER
echo   %C_BOLD%%C_YEL%📦  VÉRIFICATION DES DÉPENDANCES PYTHON%C_RST%
echo   %SEPARATOR%
call :CHECK_DEPS_INTERNAL
echo.
pause
goto :MENU_PRINCIPAL

:CHECK_DEPS_INTERNAL
echo.
call :LOGGER "  %C_BOLD%── Modules essentiels ──────────────────────────────%C_RST%"
for %%M in (flask yt_dlp playwright requests) do (
    call :LOGGER_NONL "    %%M "
    python -c "import %%M; v=getattr(%%M, '__version__', '?'); print(v)" >nul 2>&1
    if errorlevel 1 (
        call :LOGGER "%C_RED%%FAIL% Absent → pip install %%M%C_RST%"
    ) else (
        for /f "tokens=*" %%v in ('python -c "import %%M; print(getattr(%%M, \"__version__\", \"?\"))" 2^>nul') do (
            call :LOGGER "%C_GRN%%OK% v%%v%C_RST%"
        )
    )
)
call :LOGGER "  %C_BOLD%── Autres modules (standards) ───────────────────────%C_RST%"
for %%M in (urllib pathlib json logging shutil tempfile subprocess re os time) do (
    call :LOGGER_NONL "    %%M "
    python -c "import %%M" >nul 2>&1
    if errorlevel 1 (
        call :LOGGER "%C_RED%%FAIL%%C_RST%"
    ) else (
        call :LOGGER "%C_GRN%%OK%%C_RST%"
    )
)

call :LOGGER_NONL "  Modules depuis fichier   : "
python -c "import app, playlist, browser_extractor, franime_extractor, config, utils; print('ok')" >nul 2>&1
if errorlevel 1 (
    call :LOGGER "%C_RED%%FAIL% Au moins un module a un problème d'import%C_RST%"
    python -c "import app, playlist, browser_extractor, franime_extractor, config, utils" 2>> "%LOG_FILE%"
) else (
    call :LOGGER "%C_GRN%%OK% Tous les modules importent sans erreur%C_RST%"
)
goto :eof

REM ═══════════════════════════════════════════════════════════════════
REM  :CHECK_TOOLS
REM ═══════════════════════════════════════════════════════════════════
:CHECK_TOOLS
call :BANNER
echo   %C_BOLD%%C_YEL%🎬  VÉRIFICATION FFmpeg / FFprobe / aria2c%C_RST%
echo   %SEPARATOR%
call :CHECK_TOOLS_INTERNAL
echo.
pause
goto :MENU_PRINCIPAL

:CHECK_TOOLS_INTERNAL
echo.
REM ── FFmpeg
call :LOGGER_NONL "  ffmpeg.exe              : "
set "FFMPEG_FOUND="
where ffmpeg >nul 2>&1
if not errorlevel 1 (
    set "FFMPEG_FOUND=1"
    for /f "tokens=*" %%i in ('where ffmpeg 2^>nul') do (
        for /f "tokens=2,3,4 delims=- " %%a in ('ffmpeg -version 2^>^&1 ^| findstr /b "ffmpeg version"') do (
            call :LOGGER "%C_GRN%%OK% v%%a (%%i)%C_RST%"
            goto :FFMPEG_DONE
        )
    )
)
if not defined FFMPEG_FOUND (
    set "FFMPEG_BIN=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin"
    if exist "!FFMPEG_BIN!\ffmpeg.exe" (
        set "FFMPEG_FOUND=1"
        call :LOGGER "%C_GRN%%OK% Trouvé dans Winget (%%FFMPEG_BIN%%)%C_RST%"
    )
)
if not defined FFMPEG_FOUND (
    call :LOGGER "%C_RED%%FAIL% Introuvable — installer avec : winget install ffmpeg%C_RST%"
)
:FFMPEG_DONE

REM ── FFprobe
call :LOGGER_NONL "  ffprobe.exe             : "
set "FFPROBE_FOUND="
where ffprobe >nul 2>&1
if not errorlevel 1 (
    set "FFPROBE_FOUND=1"
    call :LOGGER "%C_GRN%%OK%%C_RST%"
)
if not defined FFPROBE_FOUND (
    if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffprobe.exe" (
        call :LOGGER "%C_GRN%%OK% Trouvé dans Winget%C_RST%"
    ) else (
        call :LOGGER "%C_RED%%FAIL% Introuvable — nécessaire pour les métadonnées vidéo%C_RST%"
    )
)

REM ── aria2c
call :LOGGER_NONL "  aria2c.exe              : "
set "ARIA_FOUND="
where aria2c >nul 2>&1
if not errorlevel 1 (
    set "ARIA_FOUND=1"
    for /f "tokens=3" %%v in ('aria2c --version 2^>^&1 ^| findstr /b "aria2 version"') do (
        call :LOGGER "%C_GRN%%OK% v%%v — Téléchargements parallèles activables%C_RST%"
        goto :ARIA_DONE
    )
)
if not defined ARIA_FOUND (
    for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\aria2.aria2*") do (
        for /d %%S in ("%%D\aria2*") do (
            if exist "%%S\aria2c.exe" (
                set "PATH=%%S;!PATH!"
                call :LOGGER "%C_GRN%%OK% Trouvé Winget + PATH mis à jour%C_RST%"
                set "ARIA_FOUND=1"
                goto :ARIA_DONE
            )
        )
    )
)
if not defined ARIA_FOUND (
    call :LOGGER "%C_YEL%%WARN% Absent — optionnel mais recommandé (téléchargements x16 plus rapide)%C_RST%"
    echo          Installer via : winget install aria2.aria2
)
:ARIA_DONE

REM ── Chrome
call :LOGGER_NONL "  Google Chrome           : "
set "CHROME_FOUND="
for %%P in ("%PROGRAMFILES%\Google\Chrome\Application\chrome.exe" "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe") do (
    if exist %%P (
        call :LOGGER "%C_GRN%%OK% %%~fP%C_RST%"
        set "CHROME_FOUND=1"
        goto :CHROME_DONE
    )
)
if not defined CHROME_FOUND (
    call :LOGGER "%C_YEL%%WARN% Non détecté — utile pour fallback Playwright (profil cookies)%C_RST%"
)
:CHROME_DONE
goto :eof

REM ═══════════════════════════════════════════════════════════════════
REM  :CHECK_PLAYWRIGHT
REM ═══════════════════════════════════════════════════════════════════
:CHECK_PLAYWRIGHT
call :BANNER
echo   %C_BOLD%%C_YEL%🌐  VÉRIFICATION PLAYWRIGHT + EXTRACTEUR NAVIGATEUR%C_RST%
echo   %SEPARATOR%
call :CHECK_PLAYWRIGHT_INTERNAL
echo.
pause
goto :MENU_PRINCIPAL

:CHECK_PLAYWRIGHT_INTERNAL
echo.
call :LOGGER_NONL "  Module playwright       : "
python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    call :LOGGER "%C_RED%%FAIL% Module absent → pip install playwright%C_RST%"
    goto :PW_SKIP
)
call :LOGGER "%C_GRN%%OK%%C_RST%"

call :LOGGER_NONL "  Navigateur Chromium     : "
python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); b.close(); p.stop(); print('ok')" >nul 2>&1
if errorlevel 1 (
    call :LOGGER "%C_YEL%%WARN% Chromium non installé — lancement installation..."
    echo.
    python -m playwright install chromium
    echo.
    call :LOGGER_NONL "  Chromium réessayé       : "
    python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); b.close(); p.stop(); print('ok')" >nul 2>&1
    if errorlevel 1 (
        call :LOGGER "%C_RED%%FAIL% Échec — fallback navigateur sera DISPONIBLE%C_RST%"
    ) else (
        call :LOGGER "%C_GRN%%OK% Installé et fonctionnel%C_RST%"
    )
) else (
    call :LOGGER "%C_GRN%%OK% Installé et fonctionnel%C_RST%"
)

call :LOGGER_NONL "  Test page blanche       : "
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    p1 = b.new_page()
    p1.goto('about:blank')
    t = p1.title()
    b.close()
    print('ok')
" >nul 2>&1
if errorlevel 1 (
    call :LOGGER "%C_RED%%FAIL% Impossible de charger une page simple%C_RST%"
) else (
    call :LOGGER "%C_GRN%%OK%%C_RST%"
)

call :LOGGER_NONL "  Browser profile dir     : "
if exist "browser_profile" (
    call :LOGGER "%C_GRN%%OK% Existe%C_RST%"
) else (
    mkdir browser_profile
    call :LOGGER "%C_GRN%%OK% Créé%C_RST%"
)

:PW_SKIP
goto :eof

REM ═══════════════════════════════════════════════════════════════════
REM  :TEST_YTDLP — Test téléchargement YouTube
REM ═══════════════════════════════════════════════════════════════════
:TEST_YTDLP
call :BANNER
echo   %C_BOLD%%C_YEL%🧪  TEST YT-DLP (vidéo courte YouTube)%C_RST%
echo   %SEPARATOR%
echo.
call :LOGGER "  Test : simulation extraction metadata YouTube..."
set "TEST_URL=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
call :LOGGER "  URL de test : %TEST_URL%"
echo.

python -c "
import sys, json
import yt_dlp
ydl_opts = {
    'quiet': True,
    'no_warnings': False,
    'skip_download': True,
    'noplaylist': True,
    'format': 'bestaudio/best',
}
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info('%TEST_URL%', download=False)
        title = info.get('title', 'N/A')
        duration = info.get('duration', 0)
        formats_count = len(info.get('formats', []))
        print('SUCCESS')
        print('  Titre   :', title)
        print('  Durée   :', duration, 'sec')
        print('  Formats :', formats_count)
except Exception as e:
    print('ERROR:', str(e))
    sys.exit(1)
" 2>&1 | tee /a "%LOG_FILE%"

set "EXITCODE=%ERRORLEVEL%"
echo.
if "%EXITCODE%"=="0" (
    call :LOGGER "  %C_GRN%✅ yt-dlp fonctionne correctement ! Extraction metadata OK.%C_RST%"
) else (
    call :LOGGER "  %C_RED%❌ yt-dlp en erreur (exit %EXITCODE%). Vérifiez réseau + pare-feu.%C_RST%"
)
echo.
pause
goto :MENU_PRINCIPAL

REM ═══════════════════════════════════════════════════════════════════
REM  :TEST_NETWORK
REM ═══════════════════════════════════════════════════════════════════
:TEST_NETWORK
call :BANNER
echo   %C_BOLD%%C_YEL%📡  TEST RÉSEAU, DNS ET CONNECTIVITÉ%C_RST%
echo   %SEPARATOR%
call :TEST_NETWORK_INTERNAL
echo.
pause
goto :MENU_PRINCIPAL

:TEST_NETWORK_INTERNAL
echo.
call :LOGGER "  %C_BOLD%── Connectivité générale ────────────────────────────%C_RST%"
for %%H in (8.8.8.8 1.1.1.1) do (
    call :LOGGER_NONL "  Ping %%H (DNS Google/Cloudflare) : "
    ping -n 1 -w 1500 %%H >nul 2>&1
    if errorlevel 1 (
        call :LOGGER "%C_RED%%FAIL% Pas de réponse%C_RST%"
    ) else (
        call :LOGGER "%C_GRN%%OK%%C_RST%"
    )
)

call :LOGGER "  %C_BOLD%── Sites cibles DowFlow ─────────────────────────────%C_RST%"
for %%S in (
    "https://www.youtube.com"
    "https://franime.fr"
    "https://video.sibnet.ru"
    "https://filemoon.to"
) do (
    call :LOGGER_NONL "  HTTP GET %%~S "
    powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri '%%~S' -UseBasicParsing -TimeoutSec 8 -UserAgent 'Mozilla/5.0'; Write-Host ('OK '+[string]$r.StatusCode) } catch { Write-Host ('FAIL '+($_.Exception.Message -split [Environment]::NewLine)[0]) }" 2>&1 | tee /a "%LOG_FILE%"
)

call :LOGGER "  %C_BOLD%── Configuration Proxy ──────────────────────────────%C_RST%"
python -c "from config import PROXIES; print('  Configurés :', PROXIES if PROXIES else 'Aucun (direct)')" 2>> "%LOG_FILE%"
goto :eof

REM ═══════════════════════════════════════════════════════════════════
REM  :CHECK_CODEBASE
REM ═══════════════════════════════════════════════════════════════════
:CHECK_CODEBASE
call :BANNER
echo   %C_BOLD%%C_YEL%🔧  HEALTHCHECK CODEBASE + FLASK%C_RST%
echo   %SEPARATOR%
call :CHECK_CODEBASE_INTERNAL
echo.
pause
goto :MENU_PRINCIPAL

:CHECK_CODEBASE_INTERNAL
echo.
call :LOGGER "  %C_BOLD%── Fichiers essentiels ──────────────────────────────%C_RST%"
for %%F in (app.py playlist.py config.py utils.py browser_extractor.py franime_extractor.py templates\dowload.html requirements.txt) do (
    call :LOGGER_NONL "    %%F "
    if exist "%%F" (
        for %%A in ("%%F") do call :LOGGER "%C_GRN%%OK% %%~zA octets%C_RST%"
    ) else (
        call :LOGGER "%C_RED%%FAIL% Fichier manquant !%C_RST%"
    )
)

call :LOGGER "  %C_BOLD%── Url expanders ────────────────────────────────────%C_RST%"
for %%F in (url_expanders\__init__.py url_expanders\base.py url_expanders\franime.py url_expanders\youtube.py url_expanders\generic.py) do (
    call :LOGGER_NONL "    %%F "
    if exist "%%F" (
        call :LOGGER "%C_GRN%%OK%%C_RST%"
    ) else (
        call :LOGGER "%C_YEL%%WARN% Absent (optionnel)%C_RST%"
    )
)

call :LOGGER "  %C_BOLD%── Frontend config ──────────────────────────────────%C_RST%"
call :LOGGER_NONL "  Endpoint /config JSON   : "
start /b python -c "
import time, threading, requests, sys
sys.path.insert(0, '.')
from app import app
def srv():
    app.run(host='127.0.0.1', port=5099, debug=False, use_reloader=False)
t = threading.Thread(target=srv, daemon=True); t.start()
time.sleep(2)
try:
    r = requests.get('http://127.0.0.1:5099/config', timeout=5)
    j = r.json()
    print('OK — video_formats:', len(j.get('video_formats',[])), 'qualities:', len(j.get('video_qualities',[])), 'langs:', len(j.get('languages',[])))
except Exception as e:
    print('FAIL:', str(e))
" > "%TEMP%\dowflow_health.txt" 2>&1
timeout /t 5 /nobreak >nul
for /f "tokens=*" %%l in (%TEMP%\dowflow_health.txt) do call :LOGGER "%%l"
taskkill /f /im python.exe /fi "WINDOWTITLE eq *5099*" >nul 2>&1

call :LOGGER "  %C_BOLD%── Requirements.txt vs pip freeze ───────────────────%C_RST%"
python -m pip freeze 2>nul | findstr /i /c:"Flask==" /c:"yt-dlp==" /c:"playwright==" /c:"requests==" >> "%LOG_FILE%"
goto :eof

REM ═══════════════════════════════════════════════════════════════════
REM  :OPEN_FOLDERS
REM ═══════════════════════════════════════════════════════════════════
:OPEN_FOLDERS
call :BANNER
echo   %C_BOLD%%C_YEL%📂  EXPLORATEUR DOSSIERS%C_RST%
echo   %SEPARATOR%
echo.
echo   %C_CYN%1%C_RST% - Ouvrir logs\        (rapports de debug)
echo   %C_CYN%2%C_RST% - Ouvrir downloads\   (vidéos téléchargées)
echo   %C_CYN%3%C_RST% - Ouvrir dossier projet
echo   %C_CYN%4%C_RST% - Retour menu principal
echo.
set "CHOIX2="
set /p "CHOIX2=  ➜ Option : "
if "%CHOIX2%"=="1" ( explorer "%LOG_DIR%" & goto :OPEN_FOLDERS )
if "%CHOIX2%"=="2" ( explorer "%~dp0downloads" & goto :OPEN_FOLDERS )
if "%CHOIX2%"=="3" ( explorer "%~dp0" & goto :OPEN_FOLDERS )
goto :MENU_PRINCIPAL

REM ═══════════════════════════════════════════════════════════════════
REM  :START_DEBUG — Lancer DowFlow en mode DEBUG
REM ═══════════════════════════════════════════════════════════════════
:START_DEBUG
call :BANNER
echo   %C_BOLD%%C_YEL%🚀  DÉMARRAGE DOWFLOW EN MODE DEBUG%C_RST%
echo   %SEPARATOR%
echo.

REM ── Active venv
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM ── FFmpeg PATH
set "FFMPEG_BIN=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin"
if exist "%FFMPEG_BIN%\ffmpeg.exe" set "PATH=%FFMPEG_BIN%;%PATH%"

REM ── aria2c PATH
for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\aria2.aria2*") do (
    for /d %%S in ("%%D\aria2*") do (
        if exist "%%S\aria2c.exe" set "PATH=%%S;%PATH%"
    )
)

REM ── Variables debug
set FLASK_APP=app.py
set FLASK_DEBUG=1
set DOWFLOW_DEBUG=1
set PYTHONUNBUFFERED=1

call :LOGGER "  FLASK_APP       = %FLASK_APP%"
call :LOGGER "  FLASK_DEBUG     = %FLASK_DEBUG%"
call :LOGGER "  DOWFLOW_DEBUG   = 1"
call :LOGGER "  PYTHONUNBUFFERED= 1"
call :LOGGER "  PORT            = 5001"
echo.
echo   %C_GRN%  ► Ouvre ton navigateur sur : http://127.0.0.1:5001%C_RST%
echo   %C_YEL%  ► Presse Ctrl+C pour arrêter%C_RST%
echo.
echo   %SEPARATOR%

REM ── Auto-open browser
start "" http://127.0.0.1:5001

python app.py 2>&1 | tee /a "%LOG_FILE%"

echo.
echo   %C_YEL%Serveur arrêté.%C_RST%
pause
goto :MENU_PRINCIPAL

REM ═══════════════════════════════════════════════════════════════════
REM  :FIN
REM ═══════════════════════════════════════════════════════════════════
:FIN
cls
echo.
echo   %C_BOLD%%C_YEL%  👋 Merci d'avoir utilisé DowFlow Debug Center !%C_RST%
echo.
echo      Rapport sauvegardé :
echo      %LOG_FILE%
echo.
endlocal
exit /b 0
