@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 天下归一

echo ========================================
echo   天下归一 - 正在启动...
echo ========================================
echo.

REM 优先用 python，其次 py 启动器（Windows 常见）
where python >nul 2>&1
if %errorlevel% equ 0 (
    python main_tk.py
    goto :done
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 main_tk.py
    goto :done
)

echo [未找到 Python]
echo.
echo 请先安装 Python 3.10 或更高版本：
echo   https://www.python.org/downloads/
echo.
echo 安装时务必勾选： Add python.exe to PATH
echo 安装完成后，再双击本文件夹内的 run.bat
echo.
goto :done

:done
if errorlevel 1 (
  echo.
  echo ----------------------------------------
  echo 启动失败。可尝试：
  echo   1. 在本文件夹地址栏输入 cmd 回车
  echo   2. 输入: python main_tk.py
  echo   3. 把黑色窗口里的报错发给对方
  echo ----------------------------------------
)
echo.
pause
