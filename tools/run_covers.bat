@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo ==== دانلود جلد کتاب‌های کتابخانه ====
where python >nul 2>nul || (echo پایتون نصب نیست. از python.org نصبش کنید و گزینهٔ Add to PATH را بزنید. & pause & exit /b)
python -m pip install --quiet telethon pillow
if not exist tools\api.txt (
  set /p APIID=api_id را وارد کنید:
  set /p APIHASH=api_hash را وارد کنید:
  call echo %%APIID%% %%APIHASH%%> tools\api.txt
)
for /f "tokens=1,2" %%a in (tools\api.txt) do (set APIID=%%a& set APIHASH=%%b)
python tools\fetch_covers.py --api-id %APIID% --api-hash %APIHASH% %*
pause
