"""
Enkel FastAPI-server for HMS-generator.
Start med:  uvicorn server:app --reload
"""
import os
import re
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, field_validator
from supabase import create_client

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import pipeline

load_dotenv()

# ─── Konfigurasjon ────────────────────────────────────────────────────────────

_SUPABASE_URL   = os.environ["SUPABASE_URL"]
# Backend bruker service_role-nøkkelen (kun server-side). Anon kun som dev-fallback.
_SUPABASE_KEY   = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
_API_KEY        = os.environ["API_KEY"]
_FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:8000")
OUTPUT_DIR      = Path(__file__).parent / "output"
UI_DIR          = Path(__file__).parent / "ui"
UI_HTML         = UI_DIR / "index.html"

_supabase = create_client(_SUPABASE_URL, _SUPABASE_KEY)

# ─── App og middleware ────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app = FastAPI(title="HMS-generator")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

# CORS — kun tillat eget frontend-domene
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_FRONTEND_ORIGIN],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
    allow_credentials=False,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Legg til standard sikkerhetsheadere på alle svar."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # CSP: ingen inline scripts — all JS ligger i /static/app.js.
    # ('unsafe-inline' for style kreves av Tailwind Play CDN; fjernes ved statisk Tailwind-bygg.)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "
        "style-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
        "connect-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    return response


# ─── Autentisering ────────────────────────────────────────────────────────────

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Depends(_api_key_header)):
    """Verifiser at forespørselen bærer korrekt API-nøkkel."""
    if not api_key or api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Ugyldig eller manglende API-nøkkel.")
    return api_key


# ─── Inndatamodell med validering ─────────────────────────────────────────────

_INJECTION_PATTERNS = re.compile(
    r"(ignore\s+(your|all|previous|system)\s+(instructions?|prompts?)|"
    r"system\s*prompt|jailbreak|override\s+(instructions?|system)|"
    r"forget\s+(everything|all)|act\s+as\s+if|you\s+are\s+now|"
    r"new\s+persona|disregard\s+(previous|all))",
    re.IGNORECASE,
)

_ORG_NR_PATTERN = re.compile(r"^\d{9}$|^\d{3}\s\d{3}\s\d{3}$|^$")


def _sanitize(value: str, field_name: str, max_len: int) -> str:
    """Sjekk lengde og prompt injection-mønstre.

    Verdien lagres som rådata — HTML-escaping skjer ved rendering i frontend
    (DOMPurify), aldri ved lagring. Escaping her ødela bedriftsnavn med &, ' osv.
    Regex-listen er kun et sekundært lag; primærforsvaret er at brukerfelter
    sendes som avgrenset data til modellene (se pipeline._bedriftsblokk).
    """
    value = value.strip()
    if len(value) > max_len:
        raise ValueError(f"{field_name} er for lang (maks {max_len} tegn).")
    if _INJECTION_PATTERNS.search(value):
        raise ValueError(f"Ugyldig innhold i {field_name}.")
    if re.search(r"[<>{}]", value):
        raise ValueError(f"Ugyldige tegn i {field_name}.")
    return value


class SessionRequest(BaseModel):
    bedriftsnavn:             str = Field(..., min_length=1, max_length=200)
    organisasjonsnummer:      str = Field("", max_length=11)
    nace_kode:                str = Field("", max_length=15)
    bransje:                  str = Field("", max_length=150)
    antall_ansatte:           int = Field(..., ge=1, le=100_000)
    kontaktperson:            str = Field("", max_length=200)
    har_skiftarbeid:          bool = False
    har_farlige_stoffer:      bool = False
    har_tungt_arbeid:         bool = False
    har_utvidet_egenmelding:  bool = False
    spesielle_risikoer:       str = Field("", max_length=2000)
    oensker_personalhaandbok: bool = True

    @field_validator("bedriftsnavn")
    @classmethod
    def validate_bedriftsnavn(cls, v):
        return _sanitize(v, "bedriftsnavn", 200)

    @field_validator("organisasjonsnummer")
    @classmethod
    def validate_orgnr(cls, v):
        v = v.strip()
        if v and not _ORG_NR_PATTERN.match(v):
            raise ValueError("Organisasjonsnummer må være 9 siffer.")
        return v

    @field_validator("nace_kode")
    @classmethod
    def validate_nace(cls, v):
        v = v.strip()
        if v and not re.match(r"^[A-Z]\d{1,2}(\.\d{1,2})?$", v):
            raise ValueError("Ugyldig NACE-kode.")
        return v

    @field_validator("bransje")
    @classmethod
    def validate_bransje(cls, v):
        return _sanitize(v, "bransje", 150)

    @field_validator("kontaktperson")
    @classmethod
    def validate_kontaktperson(cls, v):
        return _sanitize(v, "kontaktperson", 200)

    @field_validator("spesielle_risikoer")
    @classmethod
    def validate_spesielle_risikoer(cls, v):
        return _sanitize(v, "spesielle_risikoer", 2000)


# ─── Endepunkter ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Server frontend-HTML. Ingen hemmeligheter injiseres — brukeren oppgir
    tilgangsnøkkel i UI-et, og den valideres mot /api/auth/check."""
    return HTMLResponse(content=UI_HTML.read_text(encoding="utf-8"))


@app.get("/api/auth/check")
@limiter.limit("20/minute")
async def auth_check(request: Request, _: str = Depends(require_api_key)):
    """Lar frontend validere en innskrevet tilgangsnøkkel."""
    return {"ok": True}


@app.get("/api/nace")
@limiter.limit("60/minute")
async def get_nace_options(request: Request):
    """Lever NACE-alternativer fra databasen — ingen auth nødvendig (offentlig data)."""
    result = _supabase.table("harvey_nace_krav") \
        .select("nace_kode, nace_navn, nace_hovedgruppe, risikonivaa") \
        .order("nace_kode") \
        .execute()
    return result.data or []


@app.post("/api/sessions")
@limiter.limit("10/minute")
async def create_session(
    req: SessionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    _: str = Depends(require_api_key),
):
    """Opprett sesjon og start pipeline umiddelbart."""
    company_info = req.model_dump()

    result = _supabase.table("sessions").insert({
        "company_name": req.bedriftsnavn,
        "company_info": company_info,
        "status": "pending",
    }).execute()

    session_id = result.data[0]["id"]
    background_tasks.add_task(pipeline.run, session_id)
    return {"session_id": session_id}


@app.get("/api/sessions/{session_id}")
@limiter.limit("120/minute")
async def get_session(
    session_id: str,
    request: Request,
    _: str = Depends(require_api_key),
):
    _validate_uuid(session_id)
    try:
        result = _supabase.table("sessions").select("*").eq("id", session_id).maybe_single().execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Sesjon ikke funnet")
    if not result or not result.data:
        raise HTTPException(status_code=404, detail="Sesjon ikke funnet")
    return result.data


@app.get("/api/sessions/{session_id}/runs")
@limiter.limit("120/minute")
async def get_runs(
    session_id: str,
    request: Request,
    _: str = Depends(require_api_key),
):
    _validate_uuid(session_id)
    result = _supabase.table("agent_runs").select("*").eq("session_id", session_id).execute()
    return result.data


@app.get("/api/sessions/{session_id}/handbooks")
@limiter.limit("60/minute")
async def get_handbooks(
    session_id: str,
    request: Request,
    _: str = Depends(require_api_key),
):
    _validate_uuid(session_id)
    result = _supabase.table("handbooks").select("*").eq("session_id", session_id).execute()
    return result.data


@app.get("/api/sessions/{session_id}/files")
@limiter.limit("60/minute")
async def list_files(
    session_id: str,
    request: Request,
    _: str = Depends(require_api_key),
):
    """List genererte filer (Excel, Word, Markdown) for en sesjon."""
    _validate_uuid(session_id)
    session_dir = OUTPUT_DIR / session_id
    if not session_dir.exists():
        return []

    type_map = {".xlsx": "excel", ".docx": "word", ".md": "markdown"}
    files = []
    for f in sorted(session_dir.iterdir()):
        if f.suffix in type_map:
            files.append({
                "name": f.name,
                "type": type_map[f.suffix],
                "url": f"/api/sessions/{session_id}/files/{f.name}",
            })
    return files


@app.get("/api/sessions/{session_id}/files/{filename}")
@limiter.limit("60/minute")
async def download_file(
    session_id: str,
    filename: str,
    request: Request,
    _: str = Depends(require_api_key),
):
    """Last ned en generert fil med sikkert path-oppslag."""
    _validate_uuid(session_id)
    safe_name = Path(filename).name  # Stripp evt. directory-traversal
    file_path = (OUTPUT_DIR / session_id / safe_name).resolve()

    # Verifiser at filen faktisk ligger innenfor OUTPUT_DIR / session_id
    expected_root = (OUTPUT_DIR / session_id).resolve()
    if not str(file_path).startswith(str(expected_root)):
        raise HTTPException(status_code=400, detail="Ugyldig filnavn.")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fil ikke funnet")

    return FileResponse(path=str(file_path), filename=safe_name)


# ─── Hjelpefunksjoner ─────────────────────────────────────────────────────────

_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _validate_uuid(value: str):
    if not _UUID_PATTERN.match(value):
        raise HTTPException(status_code=400, detail="Ugyldig sesjon-ID.")
