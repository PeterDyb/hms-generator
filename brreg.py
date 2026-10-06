"""
Oppslag mot Brønnøysundregistrenes åpne Enhetsregister.

Åpent API uten nøkkel: https://data.brreg.no/enhetsregisteret/api/enheter/{orgnr}

Modulen gjør to ting og ikke mer: normaliserer/validerer organisasjonsnummer,
og henter de feltene HMS-genereringen faktisk bruker. All feilhåndtering går
gjennom BrregFeil, som bærer en ferdig formulert melding til sluttbruker —
sånn at server.py slipper å oversette tekniske feil til norsk i hvert kall.
"""
from __future__ import annotations

import httpx

API_BASE = "https://data.brreg.no/enhetsregisteret/api/enheter"
TIMEOUT = 6.0

# MOD11-vekter for organisasjonsnummer, brukt på de åtte første sifrene.
_MOD11_VEKTER = (3, 2, 7, 6, 5, 4, 3, 2)


class BrregFeil(Exception):
    """
    Feil ved oppslag. `kode` er for logikk og logging, `brukermelding` er
    ferdig norsk tekst som trygt kan vises i UI.
    """

    def __init__(self, kode: str, brukermelding: str):
        super().__init__(f"{kode}: {brukermelding}")
        self.kode = kode
        self.brukermelding = brukermelding


def normaliser_orgnr(verdi: str | int | None) -> str:
    """
    Gjør «912 345 678», «912.345.678» og 912345678 om til «912345678».

    Validerer også MOD11-kontrollsifferet, slik at åpenbare tastefeil fanges
    før vi bruker et nettverkskall på dem. Kaster BrregFeil ved ugyldig nummer.
    """
    if verdi is None:
        raise BrregFeil("ugyldig_orgnr", "Organisasjonsnummer mangler.")

    siffer = "".join(t for t in str(verdi) if t.isdigit())
    if len(siffer) != 9:
        raise BrregFeil(
            "ugyldig_orgnr",
            "Organisasjonsnummer må bestå av ni siffer.",
        )

    sum_ = sum(int(s) * v for s, v in zip(siffer[:8], _MOD11_VEKTER))
    rest = sum_ % 11
    kontroll = 0 if rest == 0 else 11 - rest
    if kontroll == 10 or kontroll != int(siffer[8]):
        raise BrregFeil(
            "ugyldig_orgnr",
            "Organisasjonsnummeret er ikke gyldig — kontrollsifferet stemmer ikke. "
            "Sjekk at alle ni sifrene er riktige.",
        )
    return siffer


def _naeringskoder(data: dict) -> list[dict]:
    """
    Plukk ut naeringskode1–3 i rekkefølge. Enheten har alltid kode 1;
    kode 2 og 3 finnes bare når virksomheten har oppgitt flere næringer.
    """
    koder = []
    for n in (1, 2, 3):
        node = data.get(f"naeringskode{n}")
        if not node or not node.get("kode"):
            continue
        koder.append({
            "kode": node["kode"],
            "beskrivelse": node.get("beskrivelse", ""),
            "rekkefolge": n,
        })
    return koder


def _tolk_svar(data: dict) -> dict:
    """Oversett Brreg-responsen til feltene HMS-genereringen bruker."""
    form = data.get("organisasjonsform") or {}
    return {
        "organisasjonsnummer": data.get("organisasjonsnummer", ""),
        "navn": data.get("navn", ""),
        "naeringskoder": _naeringskoder(data),
        # antallAnsatte mangler for en del enheter — None betyr «ikke oppgitt»,
        # ikke «null ansatte». Skjemaet må da spørre brukeren.
        "antall_ansatte": data.get("antallAnsatte"),
        "organisasjonsform": form.get("kode", ""),
        "organisasjonsform_tekst": form.get("beskrivelse", ""),
        "stiftelsesdato": data.get("stiftelsesdato"),
        "under_avvikling": bool(data.get("underAvvikling")),
        "konkurs": bool(data.get("konkurs")),
    }


def slaa_opp_enhet(orgnr: str | int, klient: httpx.Client | None = None) -> dict:
    """
    Slå opp en enhet i Enhetsregisteret.

    Returnerer dict med organisasjonsnummer, navn, naeringskoder (liste),
    antall_ansatte, organisasjonsform, stiftelsesdato og statusflagg.
    Kaster BrregFeil ved ugyldig nummer, ukjent enhet eller utilgjengelig API.

    `klient` kan injiseres i test, slik at testene slipper nettverk.
    """
    nummer = normaliser_orgnr(orgnr)
    url = f"{API_BASE}/{nummer}"

    egen_klient = klient is None
    if egen_klient:
        klient = httpx.Client(timeout=TIMEOUT, headers={"Accept": "application/json"})
    try:
        svar = klient.get(url)
    except httpx.TimeoutException:
        raise BrregFeil(
            "tjeneste_utilgjengelig",
            "Brønnøysundregistrene svarte ikke i tide. Prøv igjen om litt, "
            "eller fyll inn opplysningene manuelt.",
        )
    except httpx.HTTPError:
        raise BrregFeil(
            "tjeneste_utilgjengelig",
            "Fikk ikke kontakt med Brønnøysundregistrene. Prøv igjen om litt, "
            "eller fyll inn opplysningene manuelt.",
        )
    finally:
        if egen_klient:
            klient.close()

    if svar.status_code == 404:
        raise BrregFeil(
            "ikke_funnet",
            f"Fant ingen virksomhet med organisasjonsnummer {nummer} i Enhetsregisteret.",
        )
    # 410 Gone brukes for slettede enheter — de har en gang eksistert.
    if svar.status_code == 410:
        raise BrregFeil(
            "slettet",
            f"Virksomheten med organisasjonsnummer {nummer} er slettet fra Enhetsregisteret.",
        )
    if svar.status_code >= 500:
        raise BrregFeil(
            "tjeneste_utilgjengelig",
            "Brønnøysundregistrene har en midlertidig feil. Prøv igjen om litt, "
            "eller fyll inn opplysningene manuelt.",
        )
    if svar.status_code != 200:
        raise BrregFeil(
            "tjeneste_utilgjengelig",
            f"Uventet svar fra Brønnøysundregistrene (HTTP {svar.status_code}).",
        )

    try:
        data = svar.json()
    except ValueError:
        raise BrregFeil(
            "tjeneste_utilgjengelig",
            "Brønnøysundregistrene svarte med noe annet enn gyldige data.",
        )
    return _tolk_svar(data)
