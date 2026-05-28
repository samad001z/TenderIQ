# TenderIQ web → Vercel
#
# Two paths supported:
#   (1) Token mode (preferred for CI / one-shot): set $env:VERCEL_TOKEN first.
#   (2) Interactive: run `npx vercel login` once, then this script.
#
# Either way, the script:
#   - cds into /web
#   - sets project env vars (NEXT_PUBLIC_*) pointing at Supabase + Cloud Run
#   - deploys to production
#
# Prerequisite: deploy/deploy-api.ps1 has been run and the Cloud Run URL exists.
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

# Vercel CLI via npx — no global install needed.
$VercelCmd = "npx --yes vercel@latest"
$TokenArg  = if ($env:VERCEL_TOKEN) { "--token=$env:VERCEL_TOKEN" } else { "" }

# --- Link the project (creates .vercel/project.json) ---
if (-not (Test-Path ".vercel/project.json")) {
    Write-Host "[deploy-web] Linking Vercel project (one-time)..."
    Invoke-Expression "$VercelCmd link --yes $TokenArg"
}

# --- Push env vars (production scope) ---
function Set-VercelEnv($key, $value) {
    # `vercel env add` is interactive without --force; remove then add.
    Invoke-Expression "$VercelCmd env rm $key production --yes $TokenArg 2>$null" | Out-Null
    $value | Invoke-Expression "$VercelCmd env add $key production $TokenArg"
}
Write-Host "[deploy-web] Pushing env vars..."
Set-VercelEnv "NEXT_PUBLIC_SUPABASE_URL"      $SupabaseUrl
Set-VercelEnv "NEXT_PUBLIC_SUPABASE_ANON_KEY" $SupabaseAnon
Set-VercelEnv "NEXT_PUBLIC_API_BASE_URL"      $ApiUrl

# --- Deploy to production ---
Write-Host "[deploy-web] Deploying to production..."
$Url = Invoke-Expression "$VercelCmd deploy --prod --yes $TokenArg"
Write-Host ""
Write-Host "[deploy-web] SUCCESS"
Write-Host "  Web URL : $Url"
Write-Host ""
Write-Host "Now rerun the API deploy with that URL in CORS_ORIGINS:"
Write-Host "  `$env:CORS_ORIGINS = '$Url,http://localhost:3000'"
Write-Host "  pwsh ./deploy/deploy-api.ps1"
