@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 打包「天下归一」为 exe（仅需打包者运行一次）

echo ============================================
echo   将游戏打包成 exe，发给朋友可双击即玩
echo   （无需对方安装 Python）
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [错误] 本机未安装 Python，无法打包。
        pause
        exit /b 1
    )
    set PY=py -3
) else (
    set PY=python
)

echo [1/3] 安装打包工具 PyInstaller ...
%PY% -m pip install pyinstaller -q
if errorlevel 1 (
    echo pip 安装失败，请检查网络后重试。
    pause
    exit /b 1
)

echo [2/3] 正在打包（约 1～3 分钟）...
%PY% -m PyInstaller --noconfirm --clean ^
    --onefile ^
    --windowed ^
    --name "天下归一" ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=tkinter.font ^
    main_tk.py

if errorlevel 1 (
    echo 打包失败，请把上方报错截图保留。
    pause
    exit /b 1
)

echo [3/3] 生成发布文件夹...
if not exist "发布给好友" mkdir "发布给好友"
copy /Y "dist\天下归一.exe" "发布给好友\天下归一.exe" >nul
copy /Y "给好友看-双击我玩.txt" "发布给好友\给好友看-双击我玩.txt" >nul

echo.
echo ============================================
echo   完成！
echo   请把文件夹「发布给好友」整个发给对方
echo   对方只需双击：天下归一.exe
echo ============================================
explorer "发布给好友"
pause
