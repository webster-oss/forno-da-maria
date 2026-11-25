@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Instale Python 3.12 ou superior e marque Add Python to PATH.
  echo Depois execute novamente este arquivo.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe (
  python -m venv .venv
  if errorlevel 1 goto :erro
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :erro
.venv\Scripts\python.exe manage.py migrate
if errorlevel 1 goto :erro
.venv\Scripts\python.exe manage.py popular_padaria
if errorlevel 1 goto :erro
echo.
echo Acesse http://127.0.0.1:8000/ no navegador.
echo Para encerrar, pressione Ctrl+C.
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
exit /b
:erro
echo.
echo Nao foi possivel iniciar. Confira a mensagem acima e o README.
pause
exit /b 1
