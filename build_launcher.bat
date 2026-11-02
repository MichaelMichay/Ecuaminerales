@echo off
echo ============================================
echo  Compilando ECUAMINERALES Launcher...
echo ============================================

cd /d "%~dp0"

call venv\Scripts\activate.bat

echo.
echo [1/3] Instalando dependencias...
pip install pyinstaller qrcode[pil] Pillow requests --quiet

echo.
echo [2/3] Compilando launcher.py con PyInstaller...
pyinstaller ^
  --onefile ^
  --windowed ^
  --icon=logo.ico ^
  --name=ECUAMINERALES_LAUNCHER ^
  launcher.py

echo.
echo [3/3] Verificando resultado...
if exist "dist\ECUAMINERALES_LAUNCHER.exe" (
    echo  OK - dist\ECUAMINERALES_LAUNCHER.exe generado correctamente.
) else (
    echo  ERROR - No se genero el ejecutable. Revisa los mensajes anteriores.
)

echo.
echo ============================================
echo  Listo. Copia dist\ECUAMINERALES_LAUNCHER.exe
echo  junto al ECUAMINERALES_DESKTOP.exe existente.
echo ============================================
pause
