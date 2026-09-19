param(
    [string]$Owner = "primepike52",
    [string]$Repo = "flip-calculator",
    [ValidateSet("public", "private")]
    [string]$Visibility = "public"
)

$repoDir = "C:\Users\prime\OneDrive\Documents\Concepts\repo flip"
Set-Location $repoDir

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "GitHub CLI not found. Installing..."
    winget install --id GitHub.cli -e
}

function Test-SshGitHub {
    $result = & ssh -T -o StrictHostKeyChecking=accept-new git@github.com 2>&1
    return $LASTEXITCODE -eq 0
}

Write-Host "Checking whether the repo exists on GitHub..."
$repoExists = $false
$gh repo view "$Owner/$Repo" --json name 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    $repoExists = $true
}

if (-not $repoExists) {
    Write-Host "Repository does not exist. Creating it..."
    gh auth login --hostname github.com --git-protocol https
    git branch -M main
    if ($Visibility -eq "public") {
        gh repo create "$Owner/$Repo" --source=. --remote=origin --push --public
    }
    else {
        gh repo create "$Owner/$Repo" --source=. --remote=origin --push --private
    }
    exit 0
}

Write-Host "Repository exists. Trying SSH..."
if (Test-SshGitHub) {
    Write-Host "SSH works. Pushing with SSH..."
    git branch -M main
    git remote remove origin 2>$null
    git remote add origin "git@github.com:$Owner/$Repo.git"
    git push -u origin main
    exit 0
}

Write-Host "SSH is unavailable. Falling back to HTTPS..."
Write-Host "When prompted, use GitHub username + PAT as password."
git branch -M main
git remote remove origin 2>$null
git remote add origin "https://github.com/$Owner/$Repo.git"
git push -u origin main
