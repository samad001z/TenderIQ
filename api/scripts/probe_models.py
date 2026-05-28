"""Probe which Gemini models are reachable on Vertex for this project, by region."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env.local")
gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if gac and not os.path.isabs(gac):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((ROOT / gac).resolve())

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

proj = os.environ["GCP_PROJECT_ID"]
locations = ["asia-south1", "us-central1", "global"]
models = ["gemini-2.5-pro", "gemini-2.5-flash"]

for loc in locations:
    for model in models:
        try:
            c = genai.Client(vertexai=True, project=proj, location=loc)
            r = c.models.generate_content(
                model=model,
                contents=["reply with: ok"],
                config=types.GenerateContentConfig(temperature=0),
            )
            print(f"{loc:14} {model:18} OK  -> {(r.text or '').strip()[:20]!r}")
        except Exception as e:
            msg = str(e)
            code = "404" if "404" in msg else "403" if "403" in msg else "ERR"
            print(f"{loc:14} {model:18} {code} {msg[:90]}")
