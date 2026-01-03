@echo off
echo ==========================================
echo       Fixing Git Conflict (Reset Mode)
echo ==========================================

echo.
echo 1. Aborting stuck process...
git rebase --abort 2>nul

echo.
echo 2. Syncing with GitHub (Keeping your files)...
git fetch origin
git reset --mixed origin/main

echo.
echo 3. Re-packaging your changes...
git add .
git commit -m "Resolved conflicts and updated calendar code"

echo.
echo 4. Pushing cleaned version...
git push origin main

echo.
echo ==========================================
echo           Fixed! (Press Key)
echo ==========================================
pause
