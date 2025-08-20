# setup_env.ps1
# PowerShell script to create and configure Python venv for Dodger AI

$venvPath = "dodger-ai"

if (Test-Path $venvPath) {
    Write-Output "Virtual environment '$venvPath' already exists."
    Write-Output "Activating environment..."
    & "$venvPath\Scripts\Activate.ps1"
}
else {
    Write-Output "Creating new Python environment '$venvPath'..."
    python -m venv $venvPath
    Write-Output "Activating environment..."
    & "$venvPath\Scripts\Activate.ps1"
}

# Upgrade pip
Write-Output "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Output "Installing requirements..."
    pip install -r requirements.txt
}
else {
    Write-Output "No requirements.txt found, skipping package installation."
}

Write-Output "Environment '$venvPath' is ready."
Write-Output "To activate later, run: .\$venvPath\Scripts\Activate.ps1"