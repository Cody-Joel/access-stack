# push-to-github.ps1
# Run this once to create the GitHub repo and push Access-Stack.
# Requires: gh CLI logged in (run `gh auth login` first if needed)

$ErrorActionPreference = "Stop"

Write-Host "=== Access-Stack — GitHub push script ===" -ForegroundColor Cyan

# Safety check: ensure no .env files will be committed
$envFiles = git ls-files | Where-Object { $_ -match "\.env$" -or $_ -match "\.env\." }
if ($envFiles) {
    Write-Host "ERROR: .env files are tracked by git. Remove them first:" -ForegroundColor Red
    $envFiles | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    exit 1
}

# Check for hardcoded API keys
$keyPatterns = @("sk-ant-api", "ANTHROPIC_API_KEY\s*=\s*sk", "gsk_", "AIzaSy")
$found = $false
foreach ($pat in $keyPatterns) {
    $matches = git grep -l $pat 2>$null
    if ($matches) {
        Write-Host "WARNING: Possible API key pattern '$pat' found in:" -ForegroundColor Yellow
        $matches | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
        $found = $true
    }
}
if ($found) {
    $confirm = Read-Host "Possible keys found above. Continue anyway? (type YES)"
    if ($confirm -ne "YES") { exit 1 }
}

# Check for wg0.conf (VPN private keys)
$wgFile = git ls-files | Where-Object { $_ -match "wg0\.conf" }
if ($wgFile) {
    Write-Host "ERROR: wg0.conf is tracked (contains VPN private keys). Remove it first." -ForegroundColor Red
    exit 1
}

Write-Host "Security checks passed." -ForegroundColor Green

# Stage + commit everything
git add README.md ARCHITECTURE.md FINDINGS.md OPIGUARD.md .env.example .gitignore requirements.txt models.json
git add access-stack.py Access-Stack-B.py
git add SpecStack/ Sentinel-Stack/ SkillStack/ ONNX/ samples/ compare/ tests/
git add analyze_batch.py chart_findings.py pyproject.toml

$status = git status --short
if (-not $status) {
    Write-Host "Nothing new to commit." -ForegroundColor Yellow
} else {
    git commit -m "Access-Stack v1 — LLM evaluation toolkit with SpecLab, SentinelBench, SkillStack"
    Write-Host "Committed." -ForegroundColor Green
}

# Create GitHub repo (public)
$repoExists = gh repo view CodyJoel/access-stack 2>$null
if ($repoExists) {
    Write-Host "Repo already exists at github.com/CodyJoel/access-stack" -ForegroundColor Yellow
} else {
    gh repo create CodyJoel/access-stack `
        --public `
        --description "LLM evaluation toolkit: SpecStack (value conflicts), SentinelBench (monitor blind spots), SkillStack (AI-assisted learning). PyQt5 desktop app." `
        --source . `
        --remote origin `
        --push
    Write-Host "Created and pushed: github.com/CodyJoel/access-stack" -ForegroundColor Green
    exit 0
}

# If repo already existed, set remote + push
$remotes = git remote
if ($remotes -notcontains "origin") {
    git remote add origin "https://github.com/CodyJoel/access-stack.git"
}
git branch -M main
git push -u origin main

Write-Host "Done! View at: https://github.com/CodyJoel/access-stack" -ForegroundColor Green
