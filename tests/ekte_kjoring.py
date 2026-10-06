"""Første ekte gjennomkjøring av pipelinen — ikke mock.

Oppretter én sesjon for et fiktivt elektrikerfirma (NACE 43.210, 12 ansatte)
og kjører hele Harvey → Donna → Mike → Louis → Jessica gjennom Claude API.
Skriver framdrift til stdout underveis slik at en avbrutt kjøring kan leses.
"""
import os, sys, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["MOCK_MODE"] = "false"

import pipeline
from pipeline import _supabase

BEDRIFT = {
    "bedriftsnavn": "Nordvest Elektro AS",
    "orgnr": "",
    "nace_kode": "43.210",
    "bransje": "Elektrisk installasjonsarbeid",
    "antall_ansatte": 12,
    "kontaktperson": "Peter Dyb",
    "spesielle_risikoer": "Arbeid i høyden, arbeid på elektriske anlegg, "
                          "kjøring mellom oppdragssteder",
}

print(f"modell:      {pipeline.MODEL}")
print(f"mock:        {pipeline.MOCK_MODE}")
print(f"max_tokens:  {pipeline.MAX_TOKENS}")
print("-" * 62, flush=True)

r = _supabase.table("sessions").insert({
    "company_name": BEDRIFT["bedriftsnavn"],
    "company_info": BEDRIFT,
    "status": "pending",
}).execute()
sid = r.data[0]["id"]
print(f"sesjon opprettet: {sid}", flush=True)

t0 = time.time()
try:
    pipeline.run(sid)
    print(f"\n✓ FERDIG på {time.time() - t0:.0f} sekunder", flush=True)
except Exception as e:
    print(f"\n✗ STOPPET etter {time.time() - t0:.0f} sekunder", flush=True)
    print(f"{type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
finally:
    s = _supabase.table("sessions").select("status").eq("id", sid).single().execute()
    print(f"\nsluttstatus: {s.data['status']}", flush=True)
    runs = _supabase.table("agent_runs").select("agent,status").eq("session_id", sid).execute()
    for run in runs.data or []:
        print(f"  {run['agent']:10} {run['status']}", flush=True)
    print(f"\nsesjon: {sid}", flush=True)
