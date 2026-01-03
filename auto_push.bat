@echo off
echo ==========================================
echo       Auto Push to GitHub (Start)
echo ==========================================

:ask
set /p msg="Commit Message (Enter to default 'Update'): "
if "%msg%"=="" set msg=Update

echo.
echo 1. Adding files...
git add .

echo.
echo 2. Committing...
git commit -m "%msg%"

echo.
echo 3. Pulling latest changes (Rebase)...
git pull origin main --rebase

echo.
echo 4. Pushing to GitHub...
git push origin main

echo.
echo ==========================================
echo           Done! (Press Key)
echo ==========================================
pause
