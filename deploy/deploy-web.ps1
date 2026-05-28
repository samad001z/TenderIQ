# TenderIQ web → Vercel
#
# Prereq: run `npx vercel login` once in your shell (browser auth), OR set
# $env:VERCEL_TOKEN to a Vercel personal token.
#
# Run from C:\bid:
#   pwsh ./deploy/deploy-web.ps1

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$WebDir  = Join-Path $RootDir "web"
$EnvFile = Join-Path $RootDir ".env.local"

# --- read NEXT_PUBLIC_* from .env.local ---
if (-not (Test-Path $EnvFile)) { throw ".env.local not found at $EnvFile" }
$envMap = @{}
foreach ($line in Get-Content $EnvFile) {
    if ($line -match '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$') {
        $envMap[$Matches[1]] = $Matches[2]
    }
}
$SupabaseUrl  = $envMap["NEXT_PUBLIC_SUPABASE_URL"]
$SupabaseAnon = $envMap["NEXT_PUBLIC_SUPABASE_ANON_KEY"]
if (-not $SupabaseUrl)  { throw "NEXT_PUBLIC_SUPABASE_URL missing from .env.local" }
if (-not $SupabaseAnon) { throw "NEXT_PUBLIC_SUPABASE_ANON_KEY missing from .env.local" }

# --- discover Cloud Run URL ---
$ApiUrl = gcloud run services describe tenderiq-api --region=asia-south1 --format="value(status.url)" 2>$null
if (-not $ApiUrl) {
    throw "Cloud Run service 'tenderiq-api' not found. Run deploy/deploy-api.ps1 first."
}
Write-Host "[deploy-web] API URL: $ApiUrl"

Set-Location $WebDir

# Build the vercel argument list once.
$VercelExe  = "npx"
$VercelBase = @("--yes", "vercel@latest")
$TokenArgs  = if ($env:VERCEL_TOKEN) { @("--token=$($env:VERCEL_TOKEN)") } else { @() }

function Run-Vercel {
    param([string[]]$Args, [string]$StdinValue = $null)
    $allArgs = $VercelBase + $Args + $TokenArgs
    if ($null -ne $StdinValue) {
        $StdinValue | & $VercelExe @allArgs
    } else {
        & $VercelExe @allArgs
    }
}

# --- Link the project (creates .vercel/project.json) ---
if (-not (Test-Path ".vercel/project.json")) {
    Write-Host "[deploy-web] Linking Vercel project (one-time)..."
    Run-Vercel @("link", "--yes")
}

# --- Push env vars (production scope) ---
function Set-VercelEnv {
    param([string]$Key, [string]$Value)
    # Remove existing first; ignore failure if the var doesn't exist yet.
    try {
        Run-Vercel @("env", "rm", $Key, "production", "--yes") 2>$null | Out-Null
    } catch { }
    Run-Vercel @("env", "add", $Key, "production") $Value | Out-Null
    Write-Host "  + $Key"
}

Write-Host "[deploy-web] Pushing env vars to production scope..."
Set-VercelEnv "NEXT_PUBLIC_SUPABASE_URL"      $SupabaseUrl
Set-VercelEnv "NEXT_PUBLIC_SUPABASE_ANON_KEY" $SupabaseAnon
Set-VercelEnv "NEXT_PUBLIC_API_BASE_URL"      $ApiUrl

# --- Deploy to production ---
Write-Host "[deploy-web] Deploying to production..."
$Url = Run-Vercel @("deploy", "--prod", "--yes")
Write-Host ""
Write-Host "[deploy-web] SUCCESS"
Write-Host "  Web URL : $Url"
Write-Host ""
Write-Host "Now rerun the API deploy with that URL in CORS_ORIGINS:"
Write-Host "  `$env:CORS_ORIGINS = '$Url,http://localhost:3000'"
Write-Host "  pwsh ./deploy/deploy-api.ps1"
