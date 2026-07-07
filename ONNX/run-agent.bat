@echo off
REM Docker Agent for ONNX — Interactive & Headless Examples
REM Uses Ollama (http://localhost:11434) — No API key needed!

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  Docker Agent for ONNX (Ollama - No API Key Required)     ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check if Ollama is running
echo Checking if Ollama is running at http://localhost:11434...
powershell -Command "try { $null = Invoke-WebRequest http://localhost:11434/api/tags -TimeoutSec 2 } catch { exit 1 }" >nul 2>&1

if errorlevel 1 (
    echo ERROR: Ollama not running!
    echo.
    echo Start it:
    echo   cd C:\pgpt
    echo   up.bat
    echo.
    pause
    exit /b 1
)

REM Change to ONNX directory
cd /d C:\AS\ONNX

REM Menu
:menu
echo.
echo Choose mode:
echo [1] Interactive TUI (recommended for development)
echo [2] Simple query (get model info)
echo [3] Benchmark query
echo [4] Run API server (port 8000)
echo [5] Multi-step workflow
echo [6] Exit
echo.

set /p choice="Enter choice (1-6): "

if "%choice%"=="1" goto interactive
if "%choice%"=="2" goto info_query
if "%choice%"=="3" goto benchmark_query
if "%choice%"=="4" goto api_server
if "%choice%"=="5" goto workflow
if "%choice%"=="6" goto end

goto menu

:interactive
echo.
echo Starting interactive agent...
echo Type your questions or /help for commands
echo.
docker agent run agent.yaml
goto menu

:info_query
echo.
echo Getting model information...
echo.
docker agent run agent.yaml "List all models in ./models and provide a summary"
goto menu

:benchmark_query
echo.
echo Running benchmark query...
echo.
docker agent run agent.yaml "Check if any models exist in ./models, and if so, benchmark the first one with 50 iterations"
goto menu

:api_server
echo.
echo Starting Docker Agent as HTTP API server on port 8000...
echo API endpoint: http://localhost:8000/v1/chat/completions
echo.
docker agent serve agent.yaml --port 8000
goto menu

:workflow
echo.
echo Running multi-step workflow...
echo.
docker agent run agent.yaml ^
  "Step 1: List all files in the C:\AS\ONNX directory" ^
  "Step 2: Check what models are available" ^
  "Step 3: Get info on the project structure"
goto menu

:end
echo.
echo Goodbye!
exit /b 0
