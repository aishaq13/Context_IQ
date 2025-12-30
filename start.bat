@echo off
REM Context IQ Quick Start Script for Windows
REM This script initializes the project with sample data

setlocal enabledelayedexpansion

echo.
echo ========================================
echo 🚀 Context IQ - Quick Start (Windows)
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker first.
    exit /b 1
)

echo ✓ Docker found
echo.

REM Check if .env exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ✓ .env created
)

echo.
echo 🐳 Starting Docker Compose services...
docker-compose up -d

echo.
echo ⏳ Waiting for services to be healthy...
echo    This may take 30-60 seconds...
echo.

REM Wait for backend
set "retry_count=0"
set "max_retries=60"

:wait_loop
if %retry_count% geq %max_retries% (
    echo ⚠️ Backend took too long to start. Check logs with:
    echo    docker-compose logs -f backend
    goto skip_health
)

for /f "tokens=*" %%i in ('curl -s http://localhost:8000/api/v1/health 2^>nul') do (
    echo ✓ Backend is ready
    goto skip_health
)

set /a retry_count+=1
if %retry_count% gtr 0 (
    if %retry_count% equ 10 echo    Still waiting... (%retry_count%/%max_retries%)
    if %retry_count% equ 20 echo    Still waiting... (%retry_count%/%max_retries%)
    if %retry_count% equ 30 echo    Still waiting... (%retry_count%/%max_retries%)
    if %retry_count% equ 40 echo    Still waiting... (%retry_count%/%max_retries%)
    if %retry_count% equ 50 echo    Still waiting... (%retry_count%/%max_retries%)
)

timeout /t 1 /nobreak >nul
goto wait_loop

:skip_health
echo.
echo ✓ All services are running!
echo.
echo ========================================
echo 📚 Context IQ is ready!
echo ========================================
echo.
echo 🌐 Access the application:
echo    • Frontend:    http://localhost:3000
echo    • Backend API: http://localhost:8000
echo    • API Docs:    http://localhost:8000/docs
echo.
echo 🛠️  Useful commands:
echo    • View logs:   docker-compose logs -f ^<service^>
echo    • Services:    docker-compose ps
echo    • Stop:        docker-compose down
echo    • Reset data:  docker-compose down -v ^&^& docker-compose up -d
echo.
echo 📖 Documentation: Read README.md for detailed setup and usage
echo.
