# setup_env.ps1
# Ensures Miniconda is installed, creates a conda env (Python 3.11),
# installs CUDA-enabled PyTorch and pip dependencies.

$ErrorActionPreference = "Stop"

$envName = "dodger_ai"
$minicondaRoot = "$env:USERPROFILE\miniconda3"
$condaHook = "$minicondaRoot\shell\condabin\conda-hook.ps1"
$condaExe = "$minicondaRoot\condabin\conda.bat"

function Ensure-Conda {
    param (
        [string]$Root,
        [string]$Hook,
        [string]$Exe
    )

    $condaAvailable = $false
    try {
        conda --version | Out-Null
        $condaAvailable = $true
    } catch {
        $condaAvailable = $false
    }

    if (-not $condaAvailable -and -not (Test-Path $Root)) {
        Write-Output "Miniconda not found. Downloading and installing..."
        $installerUrl = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
        $installerPath = "$env:TEMP\Miniconda3-latest-Windows-x86_64.exe"

        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
        & $installerPath /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /S /D=$Root
        & "$Root\condabin\conda.bat" init powershell
        & "$Root\condabin\conda.bat" init cmd.exe
        Remove-Item $installerPath -Force
    }

    if (Test-Path $Hook) {
        & $Hook | Out-Null
    } elseif (Test-Path $Exe) {
        & $Exe "shell.powershell" "hook" | Out-String | Invoke-Expression
    } else {
        throw "Conda initialization files not found. Please restart the shell and rerun."
    }
}

function Ensure-CondaEnv {
    param (
        [string]$Name,
        [string]$PythonVersion = "3.11"
    )

    $envs = (conda env list --json | ConvertFrom-Json).envs
    $exists = $envs | Where-Object { $_ -like "*\$Name" }

    if (-not $exists) {
        Write-Output "Creating conda env $Name (Python $PythonVersion)..."
        conda create -n $Name python=$PythonVersion -y
    } else {
        Write-Output "Conda env $Name already exists."
    }
}

# --- Main execution ---

Ensure-Conda -Root $minicondaRoot -Hook $condaHook -Exe $condaExe
Ensure-CondaEnv -Name $envName -PythonVersion "3.11"

Write-Output "Activating conda env $envName..."
conda activate $envName

Write-Output "Installing PyTorch with CUDA 12.1..."
conda install -y -c pytorch -c nvidia pytorch torchvision torchaudio pytorch-cuda=12.1

if (Test-Path "requirements.txt") {
    Write-Output "Installing pip requirements..."
    pip install -r requirements.txt
} else {
    Write-Output "requirements.txt not found; skipping pip install."
}

Write-Output "Setup complete. To activate later: conda activate $envName"