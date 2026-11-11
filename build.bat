@echo off
setlocal
cd /d "%~dp0"
echo === WhoWantsToBeAnExplorer: build dell'eseguibile / executable build ===

rem Python da usare: la variabile BUILD_PYTHON se impostata (es. GitHub Actions),
rem altrimenti il primo Python 3 trovato (prima le versioni piu' collaudate).
set "PY="
if defined BUILD_PYTHON set "PY=%BUILD_PYTHON%"
for %%V in (3.13 3.12 3.11 3.14) do (
  if not defined PY ( py -%%V -c "import sys" >nul 2>nul && set "PY=py -%%V" )
)
if not defined PY ( py -3 -c "import sys" >nul 2>nul && set "PY=py -3" )
if not defined PY ( python -c "import sys" >nul 2>nul && set "PY=python" )
if not defined PY (
  echo Python 3 non trovato / not found: https://www.python.org
  exit /b 1
)
echo Python: %PY%

if not exist ".venv\Scripts\python.exe" (
  echo Creo l'ambiente virtuale .venv ...
  %PY% -m venv .venv || goto :errore
)
".venv\Scripts\python.exe" -m pip install --upgrade pip || goto :errore
".venv\Scripts\python.exe" -m pip install -r requirements-build.txt || goto :errore

echo.
echo Test ...
set "SDL_VIDEODRIVER=dummy"
set "SDL_AUDIODRIVER=dummy"
".venv\Scripts\python.exe" -m unittest discover -s tests || goto :errore
set "SDL_VIDEODRIVER="
set "SDL_AUDIODRIVER="

echo.
echo Creo l'eseguibile / building the executable ...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name WhoWantsToBeAnExplorer ^
  --icon assets\icona.ico ^
  --add-data "assets;assets" ^
  main.py || goto :errore

echo.
echo Fatto / done: dist\WhoWantsToBeAnExplorer.exe
exit /b 0

:errore
echo.
echo Errore durante la build / build failed.
exit /b 1
