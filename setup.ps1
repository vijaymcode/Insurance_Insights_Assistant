# Setup script for Insurance Insights Assistant (Windows)

$ErrorActionPreference = "Stop"

Write-Host "Setting up backend..."

# Create venv if it doesn't exist
if (-not (Test-Path "backend\venv")) {
    python -m venv backend\venv
}

# Install Python dependencies
& backend\venv\Scripts\pip.exe install -r backend\requirements.txt

# Copy .env.example to .env if .env doesn't exist
if (-not (Test-Path "backend\.env")) {
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "Created backend\.env from .env.example — fill in your OPENAI_API_KEY before running."
}

Write-Host "Setting up frontend..."
Set-Location frontend
npm install
Set-Location ..

Write-Host ""
Write-Host "Setup complete. To start the app:"
Write-Host "  Backend:  backend\venv\Scripts\activate  then  python backend\app.py"
Write-Host "  Frontend: cd frontend  then  npm run dev"
