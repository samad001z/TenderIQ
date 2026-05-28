# TenderIQ API → Google Cloud Run (asia-south1)
#
# What this does:
#   1. Ensures Artifact Registry repo `tenderiq` exists in asia-south1.
#   2. Submits a Cloud Build that produces a linux/amd64 image (Dockerfile in /api).
#   3. Deploys the image to Cloud Run service `tenderiq-api` with the required env
#      vars + Supabase service-role key as a Secret Manager secret (no plaintext
#      env). The runtime service account is granted Vertex AI User so ADC works
#      without shipping gcp-key.json.
#   4. Prints the Cloud Run URL. You then paste it into the Vercel project env
#      as NEXT_PUBLIC_API_BASE_URL.
#
# Prerequisites (one-time, you run these yourself if you haven't already):
#   - gcloud auth login
#   - gcloud auth application-default login
#   - gcloud services enable run.googleapis.com artifactregistry.googleapis.com `
#         cloudbuild.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com `
#         --project bids-497610
#
# Run from C:\bid:
#   pwsh ./deploy/deploy-api.ps1

$ErrorActionPreference = "Stop"

# --- config (edit only if you re-region / rename) ---
$ProjectId   = "bids-497610"
$Region      = "asia-south1"             # Mumbai — same region as Supabase + Vertex Flash
$RepoName    = "tenderiq"
$ImageName   = "tenderiq-api"
$Service     = "tenderiq-api"
$ServiceAcct = "tenderiq-api"
$SecretName  = "supabase-service-role-key"

$RootDir = Split-Path -Parent $PSScriptRoot
# Build context is the repo root (Dockerfile + .dockerignore live there) so the
# build can include both /api and /shared.
$BuildDir = $RootDir
$EnvFile  = Join-Path $RootDir ".env.local"

# --- read SUPABASE values from .env.local without printing them ---
if (-not (Test-Path $EnvFile)) { throw ".env.local not found at $EnvFile" }
$envMap = @{}
foreach ($line in Get-Content $EnvFile) {
    if ($line -match '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$') {
        $envMap[$Matches[1]] = $Matches[2]
    }
}
$SupabaseUrl   = $envMap["SUPABASE_URL"]
$SupabaseKey   = $envMap["SUPABASE_SERVICE_ROLE_KEY"]
$NextPublicSb  = $envMap["NEXT_PUBLIC_SUPABASE_URL"]
if (-not $SupabaseUrl) { throw "SUPABASE_URL missing from .env.local" }
if (-not $SupabaseKey) { throw "SUPABASE_SERVICE_ROLE_KEY missing from .env.local" }

Write-Host "[deploy] Project=$ProjectId Region=$Region Service=$Service"
gcloud config set project $ProjectId | Out-Null

# --- Artifact Registry repo ---
Write-Host "[deploy] Ensuring Artifact Registry repo '$RepoName' in $Region..."
$repoExists = gcloud artifacts repositories describe $RepoName --location=$Region 2>$null
if (-not $repoExists) {
    gcloud artifacts repositories create $RepoName `
        --repository-format=docker `
        --location=$Region `
        --description="TenderIQ container images"
}

# --- Service account for Cloud Run runtime (ADC for Vertex) ---
$SaEmail = "$ServiceAcct@$ProjectId.iam.gserviceaccount.com"
$saExists = gcloud iam service-accounts describe $SaEmail 2>$null
if (-not $saExists) {
    Write-Host "[deploy] Creating runtime service account $ServiceAcct..."
    gcloud iam service-accounts create $ServiceAcct `
        --display-name="TenderIQ API (Cloud Run)"
}
# Vertex AI User — needed for Gemini calls. Storage Object Viewer — read-only,
# not strictly required (Supabase is the doc store), but keeps options open.
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$SaEmail" `
    --role="roles/aiplatform.user" | Out-Null
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$SaEmail" `
    --role="roles/secretmanager.secretAccessor" | Out-Null

# --- Supabase service-role key → Secret Manager (NEVER set as plain env var) ---
$secretExists = gcloud secrets describe $SecretName 2>$null
if (-not $secretExists) {
    Write-Host "[deploy] Creating Secret Manager secret '$SecretName'..."
    "y" | gcloud secrets create $SecretName --replication-policy="automatic" --quiet
}
# Write a new version every deploy — keeps rotation cheap.
$tmpKey = New-TemporaryFile
Set-Content -Path $tmpKey -Value $SupabaseKey -NoNewline -Encoding ascii
try {
    gcloud secrets versions add $SecretName --data-file=$tmpKey | Out-Null
} finally {
    Remove-Item $tmpKey -Force
}

# --- Build + push the image via Cloud Build ---
$Image = "$Region-docker.pkg.dev/$ProjectId/$RepoName/$ImageName"
Write-Host "[deploy] Building image $Image..."
gcloud builds submit $BuildDir `
    --tag=$Image `
    --region=$Region `
    --project=$ProjectId
if ($LASTEXITCODE -ne 0) { throw "Cloud Build failed (exit $LASTEXITCODE). Aborting deploy." }

# --- Deploy to Cloud Run ---
# CORS_ORIGINS is set AFTER the Vercel URL is known — pass via second invocation
# or set a permissive default for first boot.
$CorsOrigins = if ($env:CORS_ORIGINS) { $env:CORS_ORIGINS } else { "*" }

Write-Host "[deploy] Deploying to Cloud Run service '$Service'..."
gcloud run deploy $Service `
    --image=$Image `
    --region=$Region `
    --platform=managed `
    --service-account=$SaEmail `
    --allow-unauthenticated `
    --port=8080 `
    --memory=1Gi `
    --cpu=2 `
    --concurrency=20 `
    --timeout=600 `
    --min-instances=0 `
    --max-instances=3 `
    --set-env-vars="GCP_PROJECT_ID=$ProjectId,GCP_LOCATION=$Region,GEMINI_PRO_LOCATION=global,GEMINI_PRO_MODEL=gemini-2.5-pro,GEMINI_FLASH_MODEL=gemini-2.5-flash,SUPABASE_URL=$SupabaseUrl,NEXT_PUBLIC_SUPABASE_URL=$NextPublicSb,CORS_ORIGINS=$CorsOrigins" `
    --set-secrets="SUPABASE_SERVICE_ROLE_KEY=${SecretName}:latest"

$Url = gcloud run services describe $Service --region=$Region --format="value(status.url)"
Write-Host ""
Write-Host "[deploy] SUCCESS"
Write-Host "  API URL : $Url"
Write-Host "  Health  : $Url/health"
Write-Host ""
Write-Host "Next: set NEXT_PUBLIC_API_BASE_URL=$Url in Vercel, then re-run with:"
Write-Host "  `$env:CORS_ORIGINS='https://<your-vercel-app>.vercel.app,http://localhost:3000'"
Write-Host "  pwsh ./deploy/deploy-api.ps1"
