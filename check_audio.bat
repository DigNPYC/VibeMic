@echo off
chcp 65001 >nul
echo ==========================================
echo  检查 VB-Cable 音量设置
echo ==========================================
echo.
echo 正在打开声音设置...
echo.
echo 请检查以下内容：
echo 1. 找到 "CABLE Input" 设备
echo 2. 确保音量不是 0%%
echo 3. 确保没有被静音
echo.
pause

REM 打开 Windows 声音设置
start mmsys.cpl

echo.
echo 已打开声音设置窗口，请检查 VB-Cable 的音量
echo.
pause
