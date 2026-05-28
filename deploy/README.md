# Deployment

TenderIQ ships as two services:

| Layer | Platform | Region |
| --- | --- | --- |
| `/web` (Next.js) | **Vercel** | Global edge — closest user POP |
| `/api` (FastAPI) | **Google Cloud Run** | `asia-south1` (Mumbai) — same region as Supabase + Vertex Flash |
| Postgres + Auth + Storage | **Supabase** | Mumbai |
| LLM inference | **Vertex AI** | Flash `asia-south1`, Pro `global` |

Co-locating the API with Supabase + Vertex Flash keeps the per-bid review under
the 30 s p95 we observed locally — every extra ms in this loop is one the
officer feels.

## Secrets policy (no leaks)

- `.env.local` and `gcp-key.json` are gitignored and never built into the image
  (see `api/.dockerignore`).
- `SUPABASE_SERVICE_ROLE_KEY` lives in **Google Secret Manager** and is mounted
  into Cloud Run via `--set-secrets`, not `--set-env-vars`. Rotate by adding a
  new secret version.
- Vertex auth uses the Cloud Run runtime **service account** (`tenderiq-api@...`)
  with the `roles/aiplatform.user` binding — no JSON key shipped.
- Supabase **publishable key** (`NEXT_PUBLIC_*`) is safe in the browser bundle;
  RLS enforces access.
- The CI / deploy script reads secret values from `.env.local` once and uploads
  them to Secret Manager via a temp file that is deleted on every run.

## Deploy the API → Cloud Run

```pwsh
cd C:\bid
pwsh ./deploy/deploy-api.ps1
```

The script will:

1. Create Artifact Registry repo `tenderiq` in `asia-south1` (idempotent).
2. Create runtime service account `tenderiq-api@bids-497610.iam.gserviceaccount.com`
   and grant `roles/aiplatform.user` + `roles/secretmanager.secretAccessor`.
3. Push `SUPABASE_SERVICE_ROLE_KEY` to Secret Manager as `supabase-service-role-key`.
4. Submit a Cloud Build of `/api` to produce a linux/amd64 image.
5. Deploy the image to Cloud Run as `tenderiq-api` (1 GiB / 2 vCPU,
   concurrency 20, max 3 instances, 600 s timeout for the SSE review stream).
6. Print the public `https://tenderiq-api-...run.app` URL.

Once the API URL is known, set `NEXT_PUBLIC_API_BASE_URL` on Vercel (see below)
and re-run the script with `CORS_ORIGINS` pointed at your Vercel domain.

## Deploy the web → Vercel

The repo is Vercel-ready (no `vercel.json` needed — Next.js auto-detected).

1. **Import**: Create a Vercel project from this repo with **Root Directory = `web`**.
2. **Environment variables** (Production + Preview):

   | Key | Value |
   | --- | --- |
   | `NEXT_PUBLIC_SUPABASE_URL` | from `.env.local` |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | from `.env.local` (the `sb_publishable_...` value) |
   | `NEXT_PUBLIC_API_BASE_URL` | the Cloud Run URL printed by `deploy-api.ps1` |

   Anything starting with `NEXT_PUBLIC_` is part of the client bundle — only the
   publishable anon key + public URLs go there.

3. **Deploy** — the build runs `next build`. First deploy takes ~3 minutes.

After Vercel publishes a URL like `https://tenderiq.vercel.app`, redeploy the
API with that URL in `CORS_ORIGINS`:

```pwsh
$env:CORS_ORIGINS = "https://tenderiq.vercel.app,http://localhost:3000"
pwsh ./deploy/deploy-api.ps1
```

## Smoke test after deploy

```pwsh
$api = (gcloud run services describe tenderiq-api --region=asia-south1 --format='value(status.url)')
curl "$api/health"
# {"status":"ok","service":"tenderiq-api","project":"bids-497610","location":"asia-south1"}

curl -X POST "$api/test-gemini"
# {"status":"ready","model":"gemini-2.5-flash"}   ← proves Vertex ADC on Cloud Run
```

Then visit the Vercel URL, sign in as `officer@tenderiq.test` /
`TenderIQ#2026`, open the seeded tender and click **View review**.
