@echo off
chcp 65001 >nul
cd /d "%~dp0"
python main_tk.py
if errorlevel 1 (
  echo.
  echo 若提示缺少 pygame，可改用: python main_tk.py
  echo 或安装依赖: python -m pip install -r requirements.txt
)
pause
