"""
Hjemmelsregister — slår opp paragrafer i stedet for å huske dem.

Tre leveranser på rad stoppet på paragrafhenvisninger, og rotårsaken var hver
gang den samme: en modell som gjenga et paragrafnummer fra hukommelsen. Verst
var det da Louis ba Mike endre meldeplikten til Arbeidstilsynet fra § 5-2 til
§ 5-1 — fra riktig til galt — og underkjente ham i neste runde for nettopp det.
Kontrollen var ikke mer pålitelig enn det den kontrollerte.

Tabellen `lovhjemler` er kilden. Et kapittel legges alltid inn komplett, og det
er nettopp det som gjør oppslaget mulig: mangler en paragraf i et registrert
kapittel, finnes den ikke.

For lover uten kapittelprefiks i paragrafnummeret (IK-forskriften § 5,
ferieloven § 10) er HELE loven én enhet. Slike lover legges bare inn komplette.
"""
from __future__ import annotations

import re

# Hvilke ord i teksten som peker på hvilken lov. Bare paragrafer som er
# eksplisitt merket med lovnavnet kontrolleres: «§ 5-2» alene kan tilhøre
# hvilken som helst lov, og en kontroll som gjetter ville meldt gyldige hjemler
# som ukjente.
LOVNAVN: dict[str, str] = {
    "AML": r"AML|aml|[Aa]rbeidsmiljøloven",
    "IKF": r"IK-forskriften|[Ii]nternkontrollforskriften|IKF",
    "FERIEL": r"[Ff]erieloven",
    "FTRL": r"[Ff]trl\.?|[Ff]olketrygdloven",
    "LDL": r"[Ll]ikestillings- og diskrimineringsloven|LDL|[Dd]iskrimineringsloven",
    "OTPL": r"OTP-loven|OTPL|[Ll]ov om obligatorisk tjenestepensjon",
}

# Ett paragrafnummer: «2-1», «2A-7», «2 A-7», «14-12 a», «15-13a», «5», «26a».
# Bokstavsuffiks med mellomrom tillates bare for a–c, ellers ville «§ 5 i
# praksis» blitt lest som § 5i.
_NUMMER = (
    r"\d+(?:\s?[A-Z](?=-))?(?:-\d+)?"
    r"(?:[a-z]|\s[a-c])?"
    r"(?![A-Za-zÆØÅæøå0-9])"
)
# «§ 2-1», «§§ 2-1 og 3-1», «§§ 2A-1 til 2A-8, 3-1 eller 4-1»
_LISTE = rf"§§?\s*{_NUMMER}(?:\s*(?:,|og|eller|til|–)\s*{_NUMMER})*"

_LOV_RE = {
    lov: re.compile(rf"(?<![A-Za-zÆØÅæøå])(?:{navn})s?\s*({_LISTE})")
    for lov, navn in LOVNAVN.items()
}
_NUMMER_RE = re.compile(_NUMMER)

_HELE_LOVEN = "*"


def hent_register(supabase) -> dict:
    """Les hele registeret, alle lover.

    Returnerer {"lover": {kortnavn: {"paragrafer", "enheter", "navn"}}}.
    Feiler oppslaget, returneres et tomt register — da gjør porten ingenting,
    framfor å melde alt som ukjent.
    """
    try:
        rader = (
            supabase.table("lovhjemler")
            .select("lov_kortnavn, lov_navn, kapittel, paragraf, overskrift, "
                    "opphevet, verifisert_dato")
            .execute()
        ).data or []
    except Exception:
        return {"lover": {}}
    return bygg_register(rader)


def bygg_register(rader: list[dict]) -> dict:
    """Bygg oppslagsstrukturen fra rader i `lovhjemler`-formatet."""
    lover: dict[str, dict] = {}
    for rad in rader:
        lov = lover.setdefault(rad["lov_kortnavn"], {
            "navn": rad.get("lov_navn") or rad["lov_kortnavn"],
            "paragrafer": {},
            "enheter": set(),
        })
        nokkel = _normaliser(rad["paragraf"])
        lov["paragrafer"][nokkel] = rad
        lov["enheter"].add(_enhet_av(nokkel))
    return {"lover": lover}


def _normaliser(paragraf: str) -> str:
    """«§ 2A-7», «2 A-7», «§2a-7» → «2A-7»; «14-12 a» → «14-12A»."""
    return re.sub(r"\s+", "", paragraf.replace("§", "")).upper()


def _enhet_av(paragraf: str) -> str:
    """Kontrollenheten en paragraf hører til.

    «2A-7» → «2A», «15-13A» → «15». Uten bindestrek («5», «26A») er hele
    loven enheten.
    """
    return paragraf.split("-")[0] if "-" in paragraf else _HELE_LOVEN


def siterte_paragrafer(doc: str) -> list[tuple[str, str]]:
    """Alle (lov, paragraf) som er eksplisitt merket med lovnavn i teksten."""
    funnet: list[tuple[str, str]] = []
    for lov, mønster in _LOV_RE.items():
        for treff in mønster.finditer(doc):
            for nr in _NUMMER_RE.findall(treff.group(1)):
                funnet.append((lov, _normaliser(nr)))
    return funnet


def hjemmelsfeil(doc: str, register: dict) -> list[str]:
    """Paragrafer i dokumentet som registeret motsier.

    To ting meldes, og bare to — begge er oppslag, ingen skjønn:

      * en paragraf som er OPPHEVET
      * en paragraf som ikke finnes i et kapittel (eller en lov) vi har
        registrert komplett

    Paragrafer i kapitler vi ikke har registrert, sies det ingenting om. Vi vet
    ikke om de finnes, og et gjett ville vært samme feil som den vi retter.
    """
    lover = register.get("lover") or {}
    if not lover:
        return []

    feil: list[str] = []
    sett: set[tuple[str, str]] = set()

    for lov, para in siterte_paragrafer(doc):
        if (lov, para) in sett or lov not in lover:
            continue
        sett.add((lov, para))
        oppslag = lover[lov]

        rad = oppslag["paragrafer"].get(para)
        if rad:
            if rad["opphevet"]:
                feil.append(
                    f"{lov} § {para} er OPPHEVET og kan ikke siteres som gjeldende rett"
                )
            continue

        enhet = _enhet_av(para)
        if enhet in oppslag["enheter"]:
            omfang = ("loven er" if enhet == _HELE_LOVEN
                      else f"kapittel {enhet} er")
            feil.append(
                f"{lov} § {para} finnes ikke — {omfang} kontrollert mot Lovdata "
                f"i sin helhet"
            )

    return feil


def _sorteringsnøkkel(rad: dict):
    nr = _normaliser(rad["paragraf"])
    deler = nr.split("-")

    def tall_og_bokstav(s: str):
        return (int(re.sub(r"\D", "", s) or 0), re.sub(r"\d", "", s))

    if len(deler) == 1:
        return ((0, ""), tall_og_bokstav(deler[0]))
    return (tall_og_bokstav(deler[0]), tall_og_bokstav(deler[1]))


def til_promptblokk(register: dict) -> str:
    """Registeret som avgrenset data til Mike.

    Poenget er ikke å lære ham loven, men å gi ham numrene å slå opp i, slik at
    paragrafnummer kan slås opp framfor å gjenkalles. Opphevede paragrafer
    utelates — de skal ikke siteres, og porten fanger dem uansett.
    """
    lover = register.get("lover") or {}
    if not lover:
        return ""

    linjer = [
        "Kontrollert mot Lovdata. Bruk NØYAKTIG disse numrene, og skriv alltid "
        "lovnavnet foran paragrafen (f.eks. «AML § 3-1», «ferieloven § 5», "
        "«ftrl. § 8-24»). Trenger du en hjemmel som ikke står her, beskriv "
        "kravet uten paragrafnummer framfor å gjette:"
    ]
    for kortnavn, lov in lover.items():
        rader = sorted(
            (r for r in lov["paragrafer"].values() if not r["opphevet"]),
            key=_sorteringsnøkkel,
        )
        if not rader:
            continue
        linjer.append(f"\n{lov['navn']} ({kortnavn}):")
        for r in rader:
            linjer.append(f"  {r['paragraf']} — {r['overskrift']}")

    return "<lovregister>\n" + "\n".join(linjer) + "\n</lovregister>"
