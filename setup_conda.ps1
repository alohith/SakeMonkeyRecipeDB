# PowerShell script to set up SakeMonkey conda environment
# Run this from Miniconda PowerShell

Write-Host "SakeMonkey Conda Environment Setup" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

# Check if conda is available
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Conda not found. Please run this from Miniconda PowerShell." -ForegroundColor Red
    exit 1
}

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $scriptDir "environment.yml"

# Check if environment.yml exists
if (-not (Test-Path $envFile)) {
    Write-Host "Error: environment.yml not found at $envFile" -ForegroundColor Red
    exit 1
}

# Check if environment exists
$envExists = conda env list | Select-String -Pattern "SakeMonkey"

if ($envExists) {
    Write-Host "`nUpdating existing SakeMonkey conda environment..." -ForegroundColor Yellow
    conda env update -n SakeMonkey -f $envFile --prune
} else {
    Write-Host "`nCreating conda environment from environment.yml..." -ForegroundColor Yellow
    conda env create -f $envFile
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nConda environment 'SakeMonkey' updated successfully!" -ForegroundColor Green
    
    # Activate the environment
    Write-Host "`nActivating SakeMonkey environment..." -ForegroundColor Yellow
    conda activate SakeMonkey
    
    # Initialize database
    Write-Host "`nInitializing database..." -ForegroundColor Yellow
    python setup.py --skip-env
    
    Write-Host "`nSetup complete!" -ForegroundColor Green
    Write-Host "`nTo activate the environment in the future, run:" -ForegroundColor Cyan
    Write-Host "  conda activate SakeMonkey" -ForegroundColor White
    Write-Host "`nTo run the GUI application:" -ForegroundColor Cyan
    Write-Host "  python gui_app.py" -ForegroundColor White
} else {
    Write-Host "`nError updating conda environment. Please check the error messages above." -ForegroundColor Red
    exit 1
}

