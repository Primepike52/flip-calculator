param(
    [string]$Owner = "primepike52",
    [string]$Repo = "flip-calculator",
    [ValidateSet("public", "private")]
    [string]$Visibility = "public"
)

$repoDir = "C:\Users\prime\OneDrive\Documents\Concepts\repo flip"
Set-Location $repoDir

function Ensure-GitHubCli {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        Write-Host "GitHub CLI not found. Installing..."
        winget install --id GitHub.cli -e
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install GitHub CLI."
        }
    }
}

function Ensure-SSHHostKnown {
    $sshDir = Join-Path $HOME ".ssh"
    if (-not (Test-Path $sshDir)) {
        New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    }

    $knownHosts = Join-Path $sshDir "known_hosts"
    if (-not (Test-Path $knownHosts)) {
        ssh-keyscan github.com >> $knownHosts 2>$null
    }
    else {
        $lines = Get-Content $knownHosts -ErrorAction SilentlyContinue
        if ($lines -notmatch "github.com") {
            ssh-keyscan github.com >> $knownHosts 2>$null
        }
    }
}

function Test-SshGitHub {
    $result = & ssh -T -o StrictHostKeyChecking=accept-new git@github.com 2>&1
    return $LASTEXITCODE -eq 0
}

Ensure-GitHubCli

Write-Host "Checking whether the GitHub repo already exists..."
$repoExists = $false
$ghRemoteCheck = & gh repo view $Owner/$Repo --json name 2>$null
if ($LASTEXITCODE -eq 0) {
    $repoExists = $true
}

if (-not $repoExists) {
    Write-Host "GitHub repo does not exist yet. Creating it..."
    gh auth login --hostname github.com --git-protocol https
    git branch -M main
    if ($Visibility -eq "public") {
        gh repo create $Owner/$Repo --source=. --remote=origin --push --public
    }
    else {
        gh repo create $Owner/$Repo --source=. --remote=origin --push --private
    }
    exit 0
}

Write-Host "Repo already exists. Trying SSH first..."
Ensure-SSHHostKnown

if (Test-SshGitHub) {
    Write-Host "SSH is working. Pushing with SSH..."
    git branch -M main
    git remote remove origin 2>$null
    git remote add origin "git@github.com:$Owner/$Repo.git"
    git push -u origin main
    exit 0
}

Write-Host "SSH is unavailable or not configured. Falling back to HTTPS..."
Write-Host "When prompted, use your GitHub username and a Personal Access Token (PAT) as the password."
git branch -M main
git remote remove origin 2>$null
git remote add origin "https://github.com/$Owner/$Repo.git"
git push -u origin main
