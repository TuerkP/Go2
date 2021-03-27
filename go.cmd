@echo off

FOR /F "tokens=* " %%F IN ('python go2.py %*') DO (
    if exist %%F (
        cd /d %%F
    ) else (
        echo %%F
    )
)