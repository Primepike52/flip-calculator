$repoDir = "C:\Users\prime\OneDrive\Documents\Concepts\repo flip"
Set-Location $repoDir

function Ensure-SSHConfig {
    $sshDir = Join-Path $HOME ".ssh"
    if (-not (Test-Path $sshDir)) {
        New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    }

    $knownHosts = Join-Path $sshDir "known_hosts"
    if (Test-Path $knownHosts) {
        $existing = Get-Content $knownHosts -ErrorAction SilentlyContinue
        if ($existing -notmatch "github.com") {
            ssh-keyscan github.com >> $knownHosts 2>$null
        }
    }
    else {
        ssh-keyscan github.com >> $knownHosts 2>$null
    }

    $candidates = @(
        (Join-Path $sshDir "id_ed25519"),
        (Join-Path $sshDir "id_rsa"),
        (Join-Path $sshDir "id_ecdsa"),
        (Join-Path $sshDir "id_25519")
    )

    $keyPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1

    if ($keyPath) {
        try {
            ssh-add $keyPath 2>$null
        }
        catch {
            Write-Host "SSH agent not available yet; continuing with SSH config step."
        }
    }
    else {
        Write-Host "No SSH private key found in ~/.ssh. If you have one, place it there and rerun this script."
    }
}

function Push-ToGitHub {
    param([bool]$UseHttps)

    Write-Host "Checking git status..."
    git status --short

    Write-Host "Renaming branch to main..."
    git branch -M main

    if ($UseHttps) {
        Write-Host "Using HTTPS remote..."
        git remote remove origin 2>$null
        git remote add origin "https://github.com/primepike52/flip-calculator.git"
    }
    else {
        Write-Host "Using SSH remote..."
        git remote remove origin 2>$null
        git remote add origin "git@github.com:primepike52/flip-calculator.git"
    }

    Write-Host "Pushing to GitHub..."
    git push -u origin main
}

Write-Host "Ensuring GitHub SSH key/host configuration exists..."
Ensure-SSHConfig

$sshAttempt = $false
try {
    $sshTest = & ssh -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1
    if ($LASTEXITCODE -eq 0) {
        $sshAttempt = $true
    }
}
catch {
    $sshAttempt = $false
}

if ($sshAttempt) {
    Push-ToGitHub -UseHttps $false
}
else {
    Write-Host "SSH is not ready, falling back to HTTPS."
    Write-Host "If HTTPS prompts for credentials, use your GitHub username and a PAT as the password."
    Push-ToGitHub -UseHttps $true
}
