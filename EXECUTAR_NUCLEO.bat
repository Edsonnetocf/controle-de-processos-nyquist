@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Ambiente Python ausente. Consulte as instrucoes no README.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" verificar.py
if errorlevel 1 goto erro
".venv\Scripts\python.exe" executar.py
if errorlevel 1 goto erro
echo.
echo Nucleo executado. Graficos e registros estao em resultados\nucleo.
start "" "%~dp0resultados\nucleo"
pause
exit /b 0
:erro
echo A execucao encontrou um erro. Preserve a mensagem para verificacao.
pause
exit /b 1
