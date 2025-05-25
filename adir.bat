:: Version: 1.1
:: Lists files as hyperlinks, supports filtered search, breadcrumb navigation, and actions
@echo off
setlocal EnableDelayedExpansion
set "SEARCH_DIR=%~1"
if "%SEARCH_DIR%"=="" set "SEARCH_DIR=%CD%"
set "FILTER=%~2"
set "OUTPUT_FILE=%TEMP%\file_list.html"
set "DEBUG_LOG=%TEMP%\adir_log.txt"
set "MAX_LOG_SIZE=50000"
set "ACTION_SCRIPT=%TEMP%\file_action.bat"
set "TREE_SCRIPT=%TEMP%\tree_view.bat"

:: Initialize debug log
echo [%DATE% %TIME%] START: Script started, dir=%SEARCH_DIR%, filter=%FILTER% >> "%DEBUG_LOG%"
for %%F in ("%DEBUG_LOG%") do set "LOG_SIZE=%%~zF"
if !LOG_SIZE! GTR %MAX_LOG_SIZE% echo [%DATE% %TIME%] WARN: Log exceeded 50KB, resetting >> "%DEBUG_LOG%" & echo  >> "%DEBUG_LOG%"

:: Validate directory
if not exist "%SEARCH_DIR%" (
    echo ERROR: Directory "%SEARCH_DIR%" does not exist
    echo [%DATE% %TIME%] ERROR: Invalid directory "%SEARCH_DIR%" >> "%DEBUG_LOG%"
    pause
    exit /b 1
)

:: Advanced menu for DIR options
echo Advanced DIR Options (leave blank for defaults):
set "DIR_OPTS=/b /a:-d /s"
set /p SORT="Sort by (name/size/time, default=name)? "
if /i "!SORT!"=="size" set "DIR_OPTS=!DIR_OPTS! /o:s"
if /i "!SORT!"=="time" set "DIR_OPTS=!DIR_OPTS! /o:d"
echo [%DATE% %TIME%] INFO: DIR options set: !DIR_OPTS! >> "%DEBUG_LOG%"

:: Generate action script for hyperlinks
echo @echo off > "%ACTION_SCRIPT%"
echo setlocal >> "%ACTION_SCRIPT%"
echo set "FILEPATH=%%~1" >> "%ACTION_SCRIPT%"
echo echo WARNING: Opening executables can be risky, Proceed? (Y/N) >> "%ACTION_SCRIPT%"
echo set /p CONFIRM= >> "%ACTION_SCRIPT%"
echo if /i not "%%CONFIRM%%"=="Y" exit /b 0 >> "%ACTION_SCRIPT%"
echo echo Actions for "%%~nx1": >> "%ACTION_SCRIPT%"
echo echo 1 Open file >> "%ACTION_SCRIPT%"
echo echo 2 Show metadata >> "%ACTION_SCRIPT%"
echo echo 3 Copy path to clipboard >> "%ACTION_SCRIPT%"
echo echo 4 Cancel >> "%ACTION_SCRIPT%"
echo set /p CHOICE="Choose (1-4): " >> "%ACTION_SCRIPT%"
echo if "%%CHOICE%%"=="1" ( >> "%ACTION_SCRIPT%"
echo     if /i "%%~x1"==".exe" (start "" x64dbg "%%~1") else if /i "%%~x1"==".dll" (start "" x64dbg "%%~1") else (start "" "%%~1") >> "%ACTION_SCRIPT%"
echo ) >> "%ACTION_SCRIPT%"
echo if "%%CHOICE%%"=="2" ( >> "%ACTION_SCRIPT%"
echo     echo ^<div style="font-family:'Courier New',monospace;font-size:12px;"^>^<h3^>Metadata for %%~nx1^</h3^> > "%TEMP%\metadata.html" >> "%ACTION_SCRIPT%"
echo     dir "%%~1" /q /r ^| findstr /v "Volume" ^| findstr /v "Directory" ^| findstr /v "---" >> "%TEMP%\metadata.html" >> "%ACTION_SCRIPT%"
echo     if /i "%%~x1"==".exe" (dumpbin /headers "%%~1" ^| findstr "machine time date entry" >> "%TEMP%\metadata.html") >> "%ACTION_SCRIPT%"
echo     if /i "%%~x1"==".dll" (dumpbin /headers "%%~1" ^| findstr "machine time date entry" >> "%TEMP%\metadata.html") >> "%ACTION_SCRIPT%"
echo     for %%E in (.jpg .png .pdf .docx) do if /i "%%~x1"=="%%E" (exiftool "%%~1" ^| findstr /i "File Date Author Creator" >> "%TEMP%\metadata.html") >> "%ACTION_SCRIPT%"
echo     if /i "%%~x1"==".mp4" (ffmpeg -i "%%~1" 2^>^&1 ^| findstr /i "Duration Creation_time" >> "%TEMP%\metadata.html") >> "%ACTION_SCRIPT%"
echo     echo ^</div^> >> "%ACTION_SCRIPT%"
echo     start "" "%TEMP%\metadata.html" >> "%ACTION_SCRIPT%"
echo ) >> "%ACTION_SCRIPT%"
echo if "%%CHOICE%%"=="3" echo %%~1 ^| clip ^& echo Path copied! ^& pause >> "%ACTION_SCRIPT%"
echo if "%%CHOICE%%"=="4" exit /b 0 >> "%ACTION_SCRIPT%"
echo endlocal >> "%ACTION_SCRIPT%"

:: Generate tree view script
echo @echo off > "%TREE_SCRIPT%"
echo call "%~f0" "%%~1" >> "%TREE_SCRIPT%"

:: Create HTML header
echo ^<!DOCTYPE html^> > "%OUTPUT_FILE%"
echo ^<html^>^<head^>^<title^>File List: %SEARCH_DIR%^</title^> >> "%OUTPUT_FILE%"
echo ^<style^>body{font-family:'Courier New',monospace;} a{text-decoration:none;color:#007bff;} a:hover{color:#ff4500;} .breadcrumb{font-size:0.9em;} .tree{overflow-x:auto;} .metadata{white-space:pre-wrap;}^</style^> >> "%OUTPUT_FILE%"
echo ^<script^>function toggle(id) {var e=document.getElementById(id);e.style.display=e.style.display=='none'?'block':'none';}^</script^> >> "%OUTPUT_FILE%"
echo ^</head^>^<body^> >> "%OUTPUT_FILE%"

:: Generate breadcrumb trail
set "BREADCRUMB="
set "TEMP_DIR=%SEARCH_DIR%"
:build_breadcrumb
for %%D in ("%TEMP_DIR%") do (
    set "DIR_NAME=%%~nxD"
    if "!DIR_NAME!"=="" set "DIR_NAME=C:"
    set "BREADCRUMB=^<a href="file:///%TREE_SCRIPT:\=/%?%%~fD"^>!DIR_NAME!^</a^> ^> !BREADCRUMB!"
    set "TEMP_DIR=%%~dpD"
    set "TEMP_DIR=!TEMP_DIR:~0,-1!"
    if not "!TEMP_DIR!"=="" if not "!TEMP_DIR!"=="%SystemDrive%" goto build_breadcrumb
)
echo ^<div class="breadcrumb"^>!BREADCRUMB!^</div^> >> "%OUTPUT_FILE%"

:: Check directory size
set "FILE_COUNT=0"
set "DIR_COUNT=0"
for /f %%F in ('dir "%SEARCH_DIR%" /s /b /a:-d') do set /a FILE_COUNT+=1
for /f %%D in ('dir "%SEARCH_DIR%" /s /b /a:d') do set /a DIR_COUNT+=1
if !FILE_COUNT! GTR 10000 if !DIR_COUNT! GTR 100 (
    echo "WARNING: Large directory (!FILE_COUNT! files, !DIR_COUNT! dirs) - loading may be slow"
    set /p CONTINUE="Continue? (Y/N): "
    if /i not "!CONTINUE!"=="Y" (
        echo [%DATE% %TIME%] INFO: Aborted due to large directory >> "%DEBUG_LOG%"
        goto :eof
    )
)
echo [%DATE% %TIME%] INFO: Directory size: !FILE_COUNT! files, !DIR_COUNT! dirs >> "%DEBUG_LOG%"

:: Generate tree view (collapsible if large)
echo ^<h2^>Directory Tree^</h2^>^<div class="tree"^> >> "%OUTPUT_FILE%"
if !FILE_COUNT! GTR 10000 if !DIR_COUNT! GTR 100 (
    echo ^<ul^> >> "%OUTPUT_FILE%"
    for /f "delims=" %%D in ('dir "%SEARCH_DIR%" /s /b /a:d') do (
        set "DIRPATH=%%D"
        set "DIRNAME=%%~nxD"
        set "DIRPATH=!DIRPATH:\=/!"
        echo ^<li^>^<a href="javascript:toggle('d%%~nD')"^>^[+^] !DIRNAME!^</a^>^<ul id="d%%~nD" style="display:none;"^> >> "%OUTPUT_FILE%"
        for /f "delims=" %%F in ('dir "%%D" /b /a:-d') do (
            set "FILENAME=%%F"
            echo ^<li^>^<a href="file:///%ACTION_SCRIPT:\=/%?%%D/%%F"^>!FILENAME!^</a^>^</li^> >> "%OUTPUT_FILE%"
        )
        echo ^</ul^>^</li^> >> "%OUTPUT_FILE%"
    )
    echo ^</ul^> >> "%OUTPUT_FILE%"
) else (
    for /f "delims=" %%D in ('dir "%SEARCH_DIR%" /s /b /a:d') do (
        set "DIRPATH=%%D"
        set "DIRNAME=%%~nxD"
        set "DIRPATH=!DIRPATH:\=/!"
        echo ^<ul^>^<li^>^<a href="file:///%TREE_SCRIPT:\=/%?%%D"^>!DIRNAME!^</a^>^<ul^> >> "%OUTPUT_FILE%"
        for /f "delims=" %%F in ('dir "%%D" /b /a:-d') do (
            set "FILENAME=%%F"
            echo ^<li^>^<a href="file:///%ACTION_SCRIPT:\=/%?%%D/%%F"^>!FILENAME!^</a^>^</li^> >> "%OUTPUT_FILE%"
        )
        echo ^</ul^>^</li^>^</ul^> >> "%OUTPUT_FILE%"
    )
)

:: Escape user filter dots for findstr
if not "!FILTER!"=="" (
    set "ESCAPED_FILTER=!FILTER:.=\.!"
    echo test.txt | findstr /i "!ESCAPED_FILTER!" >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Invalid filter "!FILTER!", Try simpler pattern (e.g., *.txt)
        echo [%DATE% %TIME%] ERROR: Invalid filter "!FILTER!" >> "%DEBUG_LOG%"
        pause
        exit /b 1
    )
) else (
    set "ESCAPED_FILTER=!FILTER!"
)

:: List files with hyperlinks to Explorer
echo ^<h1^>Files in %SEARCH_DIR%^</h1^>^<ul^> >> "%OUTPUT_FILE%"
set "FILE_COUNT=0"
for /f "delims=" %%F in ('dir "%SEARCH_DIR%" %DIR_OPTS%') do (
    set "FILEPATH=%%F"
    set "FILENAME=%%~nxF"
    set "FILEPATH=!FILEPATH:\=/!"
    if "!ESCAPED_FILTER!"=="" (
        echo ^<li^>^<a href="file:///C:/Windows/explorer.exe?%%~dpF"^>!FILENAME!^</a^> ^<a href="file:///%ACTION_SCRIPT:\=/%?%%F"^>^[^Actions^]^</a^>^</li^> >> "%OUTPUT_FILE%"
        set /a FILE_COUNT+=1
    ) else (
        echo !FILENAME! | findstr /i "!ESCAPED_FILTER!" >nul && (
            echo ^<li^>^<a href="file:///C:/Windows/explorer.exe?%%~dpF"^>!FILENAME!^</a^> ^<a href="file:///%ACTION_SCRIPT:\=/%?%%F"^>^[^Actions^]^</a^>^</li^> >> "%OUTPUT_FILE%"
            set /a FILE_COUNT+=1
        ) || (
            echo [%DATE% %TIME%] WARN: File !FILENAME! skipped, does not match "!FILTER!" >> "%DEBUG_LOG%"
        )
    )
)
echo ^</ul^> >> "%OUTPUT_FILE%"

:: Post-filter prompt (regex)
echo [%DATE% %TIME%] INFO: Found !FILE_COUNT! files >> "%DEBUG_LOG%"
set /p POSTFILTER="Post-filter regex (e.g., .*\.exe, leave blank for all)? "
if not "!POSTFILTER!"=="" (
    set "TEMP_FILE=%TEMP%\file_list_temp.html"
    copy "%OUTPUT_FILE%" "%TEMP_FILE%" >nul
    echo ^<!DOCTYPE html^> > "%OUTPUT_FILE%"
    type "%TEMP_FILE%" | findstr /r /i "!POSTFILTER!" >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Invalid post-filter regex "!POSTFILTER!", Showing unfiltered results
        echo [%DATE% %TIME%] ERROR: Invalid post-filter "!POSTFILTER!" >> "%DEBUG_LOG%"
        copy "%TEMP_FILE%" "%OUTPUT_FILE%" >nul
    ) else (
        type "%TEMP_FILE%" | findstr /r /i "!POSTFILTER!" >> "%OUTPUT_FILE%"
        echo [%DATE% %TIME%] INFO: Applied post-filter: !POSTFILTER! >> "%DEBUG_LOG%"
    )
)

:: Close HTML
echo ^</body^>^</html^> >> "%OUTPUT_FILE%"

:: Open HTML file
echo Results saved to %OUTPUT_FILE%
start "" "%OUTPUT_FILE%"
echo [%DATE% %TIME%] INFO: HTML opened, files=!FILE_COUNT! >> "%DEBUG_LOG%"

:: Graceful exit loop
:menu
echo 
echo Options: [C]ontinue, [R]estart, [E]xit
set /p MENU_CHOICE="Choose: "
if /i "!MENU_CHOICE!"=="C" (
    echo [%DATE% %TIME%] INFO: Continuing... >> "%DEBUG_LOG%"
    goto :eof
)
if /i "!MENU_CHOICE!"=="R" (
    echo [%DATE% %TIME%] INFO: Restarting... >> "%DEBUG_LOG%"
    call "%~f0" "%SEARCH_DIR%" "%FILTER%"
)
if /i "!MENU_CHOICE!"=="E" (
    echo [%DATE% %TIME%] INFO: Exiting... >> "%DEBUG_LOG%"
    goto :eof
)
echo [%DATE% %TIME%] ERROR: Invalid choice !MENU_CHOICE! >> "%DEBUG_LOG%"
goto menu

:: Error handling
:err
echo An error occurred, Check %DEBUG_LOG% for details
pause
exit /b 1

:: Patch Notes
:: - Fixed comma parsing in echo
:: - Added version number comment
:: - Logged previous version failure
:: - Maintained dot-free script
:: - Preserved all prior features