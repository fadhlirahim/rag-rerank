# PowerShell setup script for Windows users

Write-Host "Setting up RAG Embeddings API with uv and mise..." -ForegroundColor Green

# Check if uv is installed
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..." -ForegroundColor Yellow
    irm https://astral.sh/uv/install.ps1 | iex
    Write-Host "uv installed successfully!" -ForegroundColor Green
} else {
    Write-Host "uv is already installed." -ForegroundColor Green
}

# Check if mise is installed
if (!(Get-Command mise -ErrorAction SilentlyContinue)) {
    Write-Host "Installing mise..." -ForegroundColor Yellow
    irm https://mise.jdx.dev/install.ps1 | iex
    Write-Host "mise installed successfully!" -ForegroundColor Green
} else {
    Write-Host "mise is already installed." -ForegroundColor Green
}

# Ensure the correct Python version is installed via mise
Write-Host "Installing Python via mise..." -ForegroundColor Yellow
mise install python@3.11.12

# Create virtual environment using uv
Write-Host "Creating virtual environment with uv..." -ForegroundColor Yellow
uv venv

# Install all dependencies (backend + frontend)
Write-Host "Installing all dependencies..." -ForegroundColor Yellow
mise run install-all

# Copy env.example to .env if it doesn't exist
if (!(Test-Path .env)) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item env.example .env
    Write-Host "Please edit the .env file to add your API keys." -ForegroundColor Red
}

Write-Host ""
Write-Host "Setup complete! You can now run the application using:" -ForegroundColor Green
Write-Host ""
Write-Host "Backend tasks:" -ForegroundColor White
Write-Host "  mise run start      # Start the backend server" -ForegroundColor Cyan
Write-Host "  mise run dev        # Run the backend development server" -ForegroundColor Cyan
Write-Host "  mise run test       # Run tests with verbose output" -ForegroundColor Cyan
Write-Host "  mise run lint       # Run linting checks" -ForegroundColor Cyan
Write-Host "  mise run format     # Format code and fix auto-fixable issues" -ForegroundColor Cyan
Write-Host "  mise run check      # Run type checking with explicit bases" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend tasks:" -ForegroundColor White
Write-Host "  mise run frontend-install  # Install frontend dependencies" -ForegroundColor Cyan
Write-Host "  mise run frontend-dev     # Start the frontend development server" -ForegroundColor Cyan
Write-Host "  mise run frontend-build   # Build the frontend for production" -ForegroundColor Cyan
Write-Host "  mise run frontend-preview # Preview the production build" -ForegroundColor Cyan
Write-Host ""
Write-Host "Composite tasks:" -ForegroundColor White
Write-Host "  mise run install-all     # Install all dependencies (backend + frontend)" -ForegroundColor Cyan
Write-Host "  mise run dev-all        # Start both backend and frontend development servers" -ForegroundColor Cyan
Write-Host ""
Write-Host "Don't forget to edit your .env file with your API keys!" -ForegroundColor Yellow