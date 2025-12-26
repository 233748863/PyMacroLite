@echo off
chcp 65001 >nul
title PyMacroLite 清理工具

echo ========================================
echo   PyMacroLite 清理打包文件
echo ========================================
echo.

:: 清理打包输出目录
if exist "dist" (
    echo 删除 dist\
    rmdir /s /q dist
)

if exist "dist_onefile" (
    echo 删除 dist_onefile\
    rmdir /s /q dist_onefile
)

if exist "build" (
    echo 删除 build\
    rmdir /s /q build
)

:: 清理 Nuitka 临时文件
if exist "gui.build" (
    echo 删除 gui.build\
    rmdir /s /q gui.build
)

if exist "gui.dist" (
    echo 删除 gui.dist\
    rmdir /s /q gui.dist
)

if exist "gui.onefile-build" (
    echo 删除 gui.onefile-build\
    rmdir /s /q gui.onefile-build
)

if exist "PyMacroLite.build" (
    echo 删除 PyMacroLite.build\
    rmdir /s /q PyMacroLite.build
)

if exist "PyMacroLite.dist" (
    echo 删除 PyMacroLite.dist\
    rmdir /s /q PyMacroLite.dist
)

if exist "PyMacroLite.onefile-build" (
    echo 删除 PyMacroLite.onefile-build\
    rmdir /s /q PyMacroLite.onefile-build
)

:: 清理 Python 缓存
if exist "__pycache__" (
    echo 删除 __pycache__\
    rmdir /s /q __pycache__
)

if exist "core\__pycache__" (
    echo 删除 core\__pycache__\
    rmdir /s /q core\__pycache__
)

echo.
echo ========================================
echo   清理完成！
echo ========================================
echo.

pause
