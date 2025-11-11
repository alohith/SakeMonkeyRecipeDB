# PowerShell script to update SakeMonkey conda environment packages
# Run this from Miniconda PowerShell

Write-Host "Updating SakeMonkey Conda Environment" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

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

if (-not $envExists) {
    Write-Host "Error: SakeMonkey environment not found. Please create it first." -ForegroundColor Red
    Write-Host "Run: conda env create -f environment.yml" -ForegroundColor Yellow
    exit 1
}

# Update conda environment
Write-Host "`nUpdating SakeMonkey conda environment from environment.yml..." -ForegroundColor Yellow
conda env update -n SakeMonkey -f $envFile --prune

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nConda environment 'SakeMonkey' updated successfully!" -ForegroundColor Green
    
    # Show environment info
    Write-Host "`nEnvironment location:" -ForegroundColor Cyan
    conda info --envs | Select-String -Pattern "SakeMonkey"
    
    Write-Host "`nTo activate the environment, run:" -ForegroundColor Cyan
    Write-Host "  conda activate SakeMonkey" -ForegroundColor White
} else {
    Write-Host "`nError updating conda environment. Please check the error messages above." -ForegroundColor Red
    exit 1
}

