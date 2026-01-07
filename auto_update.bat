@echo off
REM ============================================
REM  US Stock Dashboard - 로그온 시 자동 업데이트
REM  시작 프로그램 폴더에 바로가기로 등록하세요
REM ============================================

cd /d "D:\Anti_Stock\Stock_US"

REM 오늘 이미 업데이트했는지 확인
set TODAY=%date:~0,10%
set FLAGFILE=last_update.txt

if exist %FLAGFILE% (
    set /p LASTUPDATE=<%FLAGFILE%
    if "%LASTUPDATE%"=="%TODAY%" (
        echo Today's update already completed. Skipping...
        exit /b 0
    )
)

REM 로그 파일 설정
set LOGFILE=update_log.txt
echo ============================================ >> %LOGFILE%
echo Update started at %date% %time% >> %LOGFILE%
echo ============================================ >> %LOGFILE%

REM Python 가상환경 활성화 (있는 경우)
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM 업데이트 실행 (Quick 모드 - AI 분석 제외)
python update_all.py --quick >> %LOGFILE% 2>&1

REM 완료 표시
echo %TODAY% > %FLAGFILE%
echo Update completed at %date% %time% >> %LOGFILE%
echo. >> %LOGFILE%

echo Update completed successfully!
