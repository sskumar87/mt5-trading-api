@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM === CONFIGURE YOUR TUNNEL NAME HERE ===
SET TUNNEL_NAME=mt5-alerts

REM === CHECK IF CLOUDFLARE TUNNEL IS RUNNING ===
tasklist /FI "IMAGENAME eq cloudflared.exe" | find /I "cloudflared.exe" >nul

START "" cloudflared tunnel run %TUNNEL_NAME%

IF %ERRORLEVEL%==0 (
    echo =====================================================
    echo ✅ Cloudflare tunnel is already running!
    echo =====================================================
    goto END
) ELSE (
    echo =====================================================
    echo ⚠️  Cloudflare tunnel is NOT running. Starting it now...
    echo =====================================================
    START "" cloudflared tunnel run %TUNNEL_NAME%
    timeout /t 5 >nul

    REM Check again after 5 seconds
    tasklist /FI "IMAGENAME eq cloudflared.exe" | find /I "cloudflared.exe" >nul
    IF %ERRORLEVEL%==0 (
        echo =====================================================
        echo ✅ Tunnel started successfully!
        echo =====================================================
    ) ELSE (
        echo =====================================================
        echo ❌ Failed to start the Cloudflare tunnel.
        echo Please check your config or logs.
        echo =====================================================
    )
)

:END
ENDLOCAL
pause
