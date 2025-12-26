@echo off
chcp 65001 >nul
title PyMacroLite 单文件打包

echo ========================================
echo   PyMacroLite 单文件打包 (体积更小)
echo ========================================
echo.
echo [注意] 单文件模式启动较慢(需解压)，但便于分发
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    pause
    exit /b 1
)

:: 检查 Nuitka
python -c "import nuitka" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装 Nuitka...
    pip install nuitka ordered-set zstandard
)

:: 清理旧构建
if exist "dist_onefile" rmdir /s /q dist_onefile
if exist "gui.build" rmdir /s /q gui.build
if exist "gui.dist" rmdir /s /q gui.dist
if exist "gui.onefile-build" rmdir /s /q gui.onefile-build
if exist "PyMacroLite.build" rmdir /s /q PyMacroLite.build
if exist "PyMacroLite.dist" rmdir /s /q PyMacroLite.dist
if exist "PyMacroLite.onefile-build" rmdir /s /q PyMacroLite.onefile-build

echo.
echo [开始打包] 这可能需要几分钟...
echo.

python -m nuitka ^
    --onefile ^
    --windows-console-mode=disable ^
    --enable-plugin=pyside6 ^
    --include-package=core ^
    --include-data-dir=assets=assets ^
    --include-data-files=libs/WGC.dll=libs/WGC.dll ^
    --include-data-files=libs/Logitech_driver.dll=libs/Logitech_driver.dll ^
    --include-data-files=project.json=project.json ^
    --nofollow-import-to=tkinter ^
    --nofollow-import-to=unittest ^
    --nofollow-import-to=test ^
    --nofollow-import-to=setuptools ^
    --nofollow-import-to=distutils ^
    --nofollow-import-to=pip ^
    --nofollow-import-to=wheel ^
    --nofollow-import-to=pkg_resources ^
    --nofollow-import-to=torch ^
    --nofollow-import-to=torchvision ^
    --nofollow-import-to=PyQt5 ^
    --nofollow-import-to=PyQt6 ^
    --nofollow-import-to=pyautogui ^
    --output-dir=dist_onefile ^
    --output-filename=PyMacroLite.exe ^
    --company-name="PyMacroLite" ^
    --product-name="PyMacroLite" ^
    --file-version=1.0.0.0 ^
    --product-version=1.0.0 ^
    --file-description="游戏自动化脚本工具" ^
    --onefile-tempdir-spec="{TEMP}/PyMacroLite_{PID}" ^
    gui.py

if errorlevel 1 (
    echo [错误] 打包失败！
    pause
    exit /b 1
)

:: 清理
if exist "gui.build" rmdir /s /q gui.build
if exist "gui.onefile-build" rmdir /s /q gui.onefile-build

echo.
echo ========================================
echo   打包完成！
echo   输出: dist_onefile\PyMacroLite.exe
echo ========================================
echo.

pause
