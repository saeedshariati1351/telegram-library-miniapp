@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo ==== دانلود جلد کتاب‌های کتابخانه ====
set PY=py -3
py -3 --version >nul 2>nul || set PY=python
%PY% --version || (echo Python not found. Install it from python.org & pause & exit /b)
%PY% -m pip install telethon pillow
if not exist tools\api.txt (
  set /p APIID=api_id را وارد کنید:
  set /p APIHASH=api_hash را وارد کنید:
  call echo %%APIID%% %%APIHASH%%> tools\api.txt
)
for /f "tokens=1,2" %%a in (tools\api.txt) do (set APIID=%%a& set APIHASH=%%b)
%PY% tools\fetch_covers.py --api-id %APIID% --api-hash %APIHASH% %*
pause
