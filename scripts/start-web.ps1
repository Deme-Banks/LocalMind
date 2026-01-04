# LocalMind Web Server Control Script (PowerShell)
# This script starts the LocalMind web interface with multiple AI backends
# Includes: AI Chat, Text-to-Video Generation, Real-time Updates

# Change to project root directory (parent of scripts folder)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptPath "..")

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LocalMind Web Server" -ForegroundColor Cyan
Write-Host "  Multi-Backend AI Assistant" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor White
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "main.py")) {
    Write-Host "ERROR: main.py not found!" -ForegroundColor Red
    Write-Host "Please run this script from the LocalMind project directory." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"

# Quick status check
Write-Host ""
Write-Host "Checking system status..." -ForegroundColor Cyan
$status = python main.py status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Some backends may not be available" -ForegroundColor Yellow
}

# Get local IP address
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" } | Select-Object -First 1).IPAddress
if (-not $ipAddress) {
    $ipAddress = "YOUR_IP"
}

# Check for API keys
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting LocalMind Web Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Features:" -ForegroundColor Yellow
Write-Host "  - Local AI models (Ollama)" -ForegroundColor White
Write-Host "  - API models (ChatGPT, Claude, Gemini, etc.)" -ForegroundColor White
Write-Host "  - Model management and downloads" -ForegroundColor White
Write-Host "  - Professional web interface" -ForegroundColor White
Write-Host "  - Text-to-Video generation (Sora, Runway, Pika)" -ForegroundColor White
Write-Host "  - Real-time progress updates" -ForegroundColor White
Write-Host ""

# Check API keys
$apiKeys = @{
    "OPENAI_API_KEY" = "ChatGPT models"
    "ANTHROPIC_API_KEY" = "Claude models"
    "GOOGLE_API_KEY" = "Gemini models"
}

$hasApiKeys = $false
foreach ($key in $apiKeys.Keys) {
    if ($env:$key) {
        Write-Host "  [OK] $key configured - $($apiKeys[$key])" -ForegroundColor Green
        $hasApiKeys = $true
    }
}

if (-not $hasApiKeys) {
    Write-Host "  [INFO] No API keys detected" -ForegroundColor Yellow
    Write-Host "         Configure APIs: python main.py configure" -ForegroundColor Gray
    Write-Host "         Or visit: http://localhost:5000/configure" -ForegroundColor Gray
    Write-Host "         See API_CONFIGURATION.md for setup instructions" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Video Generation:" -ForegroundColor Yellow
Write-Host "  - Visit: http://localhost:5000/video" -ForegroundColor White
Write-Host "  - Supports Sora 2, Runway ML, Pika Labs" -ForegroundColor White
Write-Host "  - Real-time progress tracking" -ForegroundColor White

Write-Host ""
Write-Host "The web interface will be available at:" -ForegroundColor Yellow
Write-Host "  - Local:    http://localhost:5000" -ForegroundColor White
Write-Host "  - Network:  http://$ipAddress:5000" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the web server
python main.py web --host 0.0.0.0 --port 5000

