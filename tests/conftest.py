"""Felles oppsett for enhetstestene.

Testene kjører uten nettverk: ingen Claude-kall, ingen Supabase. pipeline.py
oppretter en Supabase-klient ved import, så miljøet settes FØR import.
load_dotenv() overstyrer ikke variabler som allerede er satt, så .env lekker
ikke inn her.
"""
import os
import re
import sys
from pathlib import Path

import pytest

ROT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROT))

os.environ["MOCK_MODE"] = "true"
os.environ["SUPABASE_URL"] = "http://localhost:54321"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-nokkel"

_KOLONNER = ["lov_kortnavn", "lov_navn", "lov_nummer", "kapittel", "paragraf",
             "overskrift", "opphevet", "kilde_url", "verifisert_dato"]


def les_migreringsrader() -> list[dict]:
    """Radene i lovhjemler slik migreringene legger dem inn — 005 overstyrer 004."""
    rader: dict[tuple[str, str], dict] = {}
    for fil in sorted((ROT / "migrations").glob("00[45]_*.sql")):
        for m in re.finditer(r"^  \(('.*)\),?$", fil.read_text(encoding="utf-8"), re.M):
            verdier = re.findall(r"'((?:[^']|'')*)'|(true|false)", m.group(1))
            v = [a.replace("''", "'") if not b else b == "true" for a, b in verdier]
            assert len(v) == len(_KOLONNER), f"{fil.name}: {m.group(1)}"
            rad = dict(zip(_KOLONNER, v))
            rader[(rad["lov_kortnavn"], rad["paragraf"])] = rad
    return list(rader.values())


@pytest.fixture(scope="session")
def supabase():
    """Ekte Supabase for integrasjonstestene i test_nace_kravmotor.py.

    Hoppes over uten HMS_INTEGRASJON=1 — standardkjøringen skal gå uten
    nettverk. Leser .env direkte, siden miljøet over er satt til en falsk URL.
    """
    if os.environ.get("HMS_INTEGRASJON") != "1":
        pytest.skip("integrasjonstest — kjør med HMS_INTEGRASJON=1")
    from dotenv import dotenv_values
    from supabase import create_client
    env = dotenv_values(ROT / ".env")
    url, key = env.get("SUPABASE_URL"), env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        pytest.skip("SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY mangler i .env")
    return create_client(url, key)


@pytest.fixture(scope="session")
def rader():
    return les_migreringsrader()


@pytest.fixture(scope="session")
def register(rader):
    import lovregister
    return lovregister.bygg_register(rader)
