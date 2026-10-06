"""
Tester for den NACE-baserte kravmotoren: org.nr inn → NACE-kode og
forskriftsliste ut, for bransjer på ulike risikonivåer.

Brreg-laget stubbes med ekte responsstruktur, slik at testene kan kjøres uten
nettverk og gir samme svar hver gang. Kjøres med `pytest tests/` eller direkte
med `python tests/test_nace_kravmotor.py`.

Databasen treffes ekte via Supabase — det er nettopp koblingen mellom
NACE-kode og hjemler vi vil verifisere. Mangler miljøvariablene, hoppes de
testene over i stedet for å feile.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import brreg
import nace_krav


# ─── Stub av Brønnøysund ─────────────────────────────────────────────────────

class FalskSvar:
    def __init__(self, status_code: int, data: dict | None = None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data


class FalskKlient:
    """Erstatter httpx.Client. Svarer ut fra organisasjonsnummeret i URL-en."""

    def __init__(self, svar_per_orgnr: dict):
        self.svar = svar_per_orgnr
        self.kalte_urler: list[str] = []

    def get(self, url):
        self.kalte_urler.append(url)
        orgnr = url.rstrip("/").split("/")[-1]
        if orgnr not in self.svar:
            return FalskSvar(404)
        return FalskSvar(200, self.svar[orgnr])

    def close(self):
        pass


def _enhet(orgnr: str, navn: str, nace: list[tuple[str, str]],
           ansatte: int | None = 12) -> dict:
    """Bygg en Brreg-respons med samme feltnavn som det ekte API-et bruker."""
    data = {
        "organisasjonsnummer": orgnr,
        "navn": navn,
        "antallAnsatte": ansatte,
        "organisasjonsform": {"kode": "AS", "beskrivelse": "Aksjeselskap"},
        "stiftelsesdato": "2015-03-01",
        "underAvvikling": False,
        "konkurs": False,
    }
    for i, (kode, beskrivelse) in enumerate(nace, start=1):
        data[f"naeringskode{i}"] = {"kode": kode, "beskrivelse": beskrivelse}
    return data


# Tre bransjer på ulike risikonivåer, pluss ett tilfelle med to næringskoder.
BEDRIFTER = {
    # Lav risiko — kontor/IT
    "915772137": _enhet("915772137", "NORDVEST DIGITAL AS",
                        [("62.010", "Programmeringstjenester")], ansatte=8),
    # Høy risiko — bygg
    "923609016": _enhet("923609016", "FJORDBYGG AS",
                        [("41.200", "Oppføring av bygninger")], ansatte=34),
    # Høy risiko — renhold, med servering som sekundærnæring
    "914778271": _enhet("914778271", "RENT OG PENT AS",
                        [("81.210", "Rengjøring av bygninger"),
                         ("56.101", "Drift av restauranter og kafeer")], ansatte=22),
}


# ─── Testrammeverk ───────────────────────────────────────────────────────────

_feil: list[str] = []


def sjekk(navn: str, betingelse: bool, detalj: str = "") -> None:
    if betingelse:
        print(f"  BESTÅTT  {navn}")
    else:
        print(f"  FEILET   {navn}" + (f" — {detalj}" if detalj else ""))
        _feil.append(navn)
        # Under pytest må en feilet sjekk feile testen — ellers blir den bare
        # en utskrift ingen leser.
        if "PYTEST_CURRENT_TEST" in os.environ:
            raise AssertionError(f"{navn}" + (f" — {detalj}" if detalj else ""))


def _supabase_klient():
    """Ekte Supabase-klient, eller None hvis miljøvariablene mangler."""
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    except ImportError:
        pass
    url = os.environ.get("SUPABASE_URL")
    # Kravmotoren bare leser, og anon har lesetilgang til begge tabellene.
    # Da trenger ikke testene service_role — en tom anon-nøkkel duger òg som
    # signal om at miljøet ikke er satt opp.
    key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
           or os.environ.get("SUPABASE_ANON_KEY"))
    if not url or not key or "dummy" in url:
        return None
    from supabase import create_client
    return create_client(url, key)


# ─── 1. Oppslag og validering ────────────────────────────────────────────────

def test_orgnr_validering():
    print("\n[1] Organisasjonsnummer valideres før nettverkskall")
    sjekk("mellomrom og punktum fjernes",
          brreg.normaliser_orgnr("974 760 673") == "974760673")
    sjekk("heltall godtas", brreg.normaliser_orgnr(974760673) == "974760673")

    for ugyldig, grunn in (("912345678", "feil kontrollsiffer"),
                           ("12345", "for kort"),
                           ("", "tomt"),
                           (None, "None")):
        try:
            brreg.normaliser_orgnr(ugyldig)
            sjekk(f"avviser {grunn}", False, "ble godtatt")
        except brreg.BrregFeil as e:
            sjekk(f"avviser {grunn}", e.kode == "ugyldig_orgnr", e.kode)


def test_feilhaandtering():
    print("\n[2] Feil håndteres med brukervennlig melding")
    klient = FalskKlient(BEDRIFTER)
    try:
        # Gyldig kontrollsiffer, men ikke i registeret.
        brreg.slaa_opp_enhet("974760673", klient=klient)
        sjekk("ukjent selskap gir ikke_funnet", False, "ingen feil kastet")
    except brreg.BrregFeil as e:
        sjekk("ukjent selskap gir ikke_funnet", e.kode == "ikke_funnet", e.kode)
        sjekk("meldingen er på norsk og nevner nummeret",
              "974760673" in e.brukermelding and "Fant ingen" in e.brukermelding)

    class NedeKlient:
        def get(self, url):
            return FalskSvar(503)

        def close(self):
            pass

    try:
        brreg.slaa_opp_enhet("923609016", klient=NedeKlient())
        sjekk("API nede gir tjeneste_utilgjengelig", False, "ingen feil kastet")
    except brreg.BrregFeil as e:
        sjekk("API nede gir tjeneste_utilgjengelig",
              e.kode == "tjeneste_utilgjengelig", e.kode)
        sjekk("melding foreslår manuell utfylling",
              "manuelt" in e.brukermelding)


def test_felter_hentes_ut():
    print("\n[3] Riktige felter hentes fra Enhetsregisteret")
    klient = FalskKlient(BEDRIFTER)
    enhet = brreg.slaa_opp_enhet("914778271", klient=klient)
    sjekk("navn", enhet["navn"] == "RENT OG PENT AS")
    sjekk("antall ansatte", enhet["antall_ansatte"] == 22)
    sjekk("organisasjonsform", enhet["organisasjonsform"] == "AS")
    sjekk("stiftelsesdato", enhet["stiftelsesdato"] == "2015-03-01")
    sjekk("begge næringskoder med rekkefølge",
          [k["kode"] for k in enhet["naeringskoder"]] == ["81.210", "56.101"],
          str(enhet["naeringskoder"]))


# ─── 2. Hele kjeden: org.nr → forskriftsliste ────────────────────────────────

def test_hele_kjeden(supabase):
    print("\n[4] Hele kjeden: org.nr inn → NACE og forskrifter ut")
    klient = FalskKlient(BEDRIFTER)

    # ── Lav risiko: programmeringstjenester ──
    r = nace_krav.krav_for_orgnr("915772137", supabase, klient=klient)
    b = r["bransje"]
    sjekk("62.010 → riktig NACE-kode", b["nace_kode"] == "62.010", b["nace_kode"])
    sjekk("62.010 → lavt risikonivå", b["risikonivaa"] == "lavt", str(b["risikonivaa"]))
    sjekk("62.010 → BHT vurdert til nei",
          b["bht_paakrevd"] is False and not b["bht_maa_vurderes"])
    sjekk("62.010 → har forskriftshjemler", len(b["forskriftskrav"]) >= 2,
          str(len(b["forskriftskrav"])))
    sjekk("62.010 → ingen byggherreforskrift",
          not any("Byggherre" in f["forskrift_navn"] for f in b["forskriftskrav"]))

    # ── Høy risiko: bygg ──
    r = nace_krav.krav_for_orgnr("923609016", supabase, klient=klient)
    b = r["bransje"]
    sjekk("41.200 → riktig NACE-kode", b["nace_kode"] == "41.200", b["nace_kode"])
    sjekk("41.200 → høyt risikonivå", b["risikonivaa"] == "høyt", str(b["risikonivaa"]))
    sjekk("41.200 → BHT påkrevd", b["bht_paakrevd"] is True)
    numre = {f["forskrift_nummer"] for f in b["forskriftskrav"]}
    sjekk("41.200 → byggherreforskriften med riktig FOR-nummer",
          "FOR-2009-08-03-1028" in numre, str(numre))
    paragrafer = {f["paragraf"] for f in b["forskriftskrav"]}
    sjekk("41.200 → SHA-plan (§ 7) er med", "§ 7" in paragrafer, str(paragrafer))
    sjekk("41.200 → forhåndsmelding (§ 10) er med", "§ 10" in paragrafer)
    sjekk("41.200 → SHA-plan i dokumentkrav", "SHA-plan" in b["dokumentkrav"],
          str(b["dokumentkrav"]))

    # ── Høy risiko: renhold, med sekundærnæring servering ──
    r = nace_krav.krav_for_orgnr("914778271", supabase, klient=klient)
    b = r["bransje"]
    sjekk("81.210 → riktig NACE-kode", b["nace_kode"] == "81.210", b["nace_kode"])
    numre = {f["forskrift_nummer"] for f in b["forskriftskrav"]}
    sjekk("81.210 → godkjenningsforskrift for renhold",
          "FOR-2012-05-08-408" in numre, str(numre))
    sjekk("81.210 → HMS-kort i dokumentkrav",
          any("HMS-kort" in d for d in b["dokumentkrav"]), str(b["dokumentkrav"]))

    sjekk("sekundærnæring 56.101 er med", len(r["sekundaerbransjer"]) == 1,
          str(len(r["sekundaerbransjer"])))
    if r["sekundaerbransjer"]:
        s = r["sekundaerbransjer"][0]
        s_numre = {f["forskrift_nummer"] for f in s["forskriftskrav"]}
        sjekk("56.101 → næringsmiddelhygiene (HACCP)",
              "FOR-2008-12-22-1623" in s_numre, str(s_numre))


def test_udekket_kode(supabase):
    print("\n[5] Udekket NACE-kode dikter ikke opp hjemler")
    b = nace_krav.hent_bransjekrav("99.999", supabase)
    sjekk("dekning = ingen", b["dekning"] == nace_krav.DEKNING_INGEN, b["dekning"])
    sjekk("tom forskriftsliste", b["forskriftskrav"] == [])
    sjekk("BHT markert som uavklart", b["bht_maa_vurderes"] is True)

    blokk = nace_krav.til_promptblokk(b)
    sjekk("promptblokken advarer mot å gjette",
          "INGEN verifiserte bransjekrav" in blokk and "krever_manuell_vurdering" in blokk)


def test_promptblokk(supabase):
    print("\n[6] Promptblokken er avgrenset data med nøyaktige hjemler")
    b = nace_krav.hent_bransjekrav("41.200", supabase)
    blokk = nace_krav.til_promptblokk(b)
    sjekk("avgrenset med <bransjekrav>",
          blokk.startswith("<bransjekrav>") and blokk.endswith("</bransjekrav>"))
    sjekk("FOR-nummer med i teksten", "FOR-2009-08-03-1028" in blokk)
    sjekk("ber om nøyaktig gjenbruk", "NØYAKTIG" in blokk)
    sjekk("de gamle feilnumrene er borte",
          "FOR-2009-01-01-70" not in blokk and "FOR-2007-02-02-190" not in blokk)


def main() -> int:
    test_orgnr_validering()
    test_feilhaandtering()
    test_felter_hentes_ut()

    supabase = _supabase_klient()
    if supabase is None:
        print("\n[4-6] HOPPET OVER — SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY mangler.")
        print("      Kjør med ekte miljøvariabler for å teste hele kjeden.")
    else:
        test_hele_kjeden(supabase)
        test_udekket_kode(supabase)
        test_promptblokk(supabase)

    print()
    if _feil:
        print(f"{len(_feil)} FEILET: " + "; ".join(_feil))
        return 1
    print("ALT BESTÅTT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
