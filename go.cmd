@echo off

FOR /F "tokens=* " %%F IN ('python "%~dp0go2\go2.py" %*') DO (
    if exist "%%F" (
        cd /d "%%F"
    ) else (
        echo %%F
    )
)