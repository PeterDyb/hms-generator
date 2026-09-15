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
"""
from __future__ import annotations

import re

# Bare paragrafer som er eksplisitt merket som arbeidsmiljøloven kontrolleres.
# Dokumentene siterer også ferieloven, folketrygdloven og OTP-loven, og «§ 5-2»
# alene kan tilhøre hvilken som helst av dem. En kontroll som antar AML ville
# meldt gyldige hjemler fra andre lover som ukjente.
_AML_PARAGRAF_RE = re.compile(
    r"(?:AML|aml|[Aa]rbeidsmiljøloven)\s*§+\s*(\d+[A-Za-z]?(?:-\d+[a-z]?)?)"
)


def hent_register(supabase, lov_kortnavn: str = "AML") -> dict:
    """Les hele registeret for én lov.

    Returnerer paragrafene som oppslagstabell, og hvilke kapitler som er
    registrert. Feiler oppslaget, returneres et tomt register — da gjør porten
    ingenting, framfor å melde alt som ukjent.
    """
    try:
        rader = (
            supabase.table("lovhjemler")
            .select("kapittel, paragraf, overskrift, opphevet, verifisert_dato")
            .eq("lov_kortnavn", lov_kortnavn)
            .execute()
        ).data or []
    except Exception:
        return {"paragrafer": {}, "kapitler": set(), "lov": lov_kortnavn}

    paragrafer = {}
    kapitler = set()
    for rad in rader:
        nokkel = _normaliser(rad["paragraf"])
        paragrafer[nokkel] = rad
        kapitler.add(rad["kapittel"])
    return {"paragrafer": paragrafer, "kapitler": kapitler, "lov": lov_kortnavn}


def _normaliser(paragraf: str) -> str:
    """«§ 2A-7», «2A-7», «§2a-7» → «2A-7»."""
    return paragraf.replace("§", "").strip().upper()


def _kapittel_av(paragraf: str) -> str:
    """«2A-7» → «2A», «15-13A» → «15»."""
    return paragraf.split("-")[0]


def hjemmelsfeil(doc: str, register: dict) -> list[str]:
    """Paragrafer i dokumentet som registeret motsier.

    To ting meldes, og bare to — begge er oppslag, ingen skjønn:

      * en paragraf som er OPPHEVET
      * en paragraf som ikke finnes i et kapittel vi har registrert komplett

    Paragrafer i kapitler vi ikke har registrert, sies det ingenting om. Vi vet
    ikke om de finnes, og et gjett ville vært samme feil som den vi retter.
    """
    if not register.get("paragrafer"):
        return []

    kjente = register["paragrafer"]
    kapitler = register["kapitler"]
    lov = register.get("lov", "AML")

    feil: list[str] = []
    sett: set[str] = set()

    for treff in _AML_PARAGRAF_RE.finditer(doc):
        para = _normaliser(treff.group(1))
        if para in sett:
            continue
        sett.add(para)

        rad = kjente.get(para)
        if rad:
            if rad["opphevet"]:
                feil.append(
                    f"{lov} § {para} er OPPHEVET og kan ikke siteres som gjeldende rett"
                )
            continue

        if _kapittel_av(para) in kapitler:
            feil.append(
                f"{lov} § {para} finnes ikke — kapittel {_kapittel_av(para)} er "
                f"kontrollert mot Lovdata i sin helhet"
            )

    return feil


def til_promptblokk(register: dict, kapitler: list[str] | None = None) -> str:
    """Registeret som avgrenset data til Mike.

    Poenget er ikke å liste hele loven, men å gi de kapitlene håndbøkene
    faktisk siterer, slik at paragrafnummer kan slås opp framfor gjenkalles.
    """
    if not register.get("paragrafer"):
        return ""

    ønskede = set(kapitler) if kapitler else register["kapitler"]
    rader = [r for r in register["paragrafer"].values() if r["kapittel"] in ønskede]
    if not rader:
        return ""

    def sorteringsnøkkel(r):
        kap = r["kapittel"]
        hoved = int(re.sub(r"\D", "", kap) or 0)
        under = re.sub(r"\d", "", kap)
        nummer = _normaliser(r["paragraf"]).split("-")
        return (hoved, under, int(re.sub(r"\D", "", nummer[-1]) or 0))

    linjer = [
        f"Kontrollert mot Lovdata. Bruk NØYAKTIG disse numrene når du siterer "
        f"{register.get('lov', 'AML')}. Trenger du en hjemmel som ikke står her, "
        f"beskriv kravet uten paragrafnummer framfor å gjette:"
    ]
    forrige_kap = None
    for r in sorted(rader, key=sorteringsnøkkel):
        if r["kapittel"] != forrige_kap:
            linjer.append(f"\nKapittel {r['kapittel']}:")
            forrige_kap = r["kapittel"]
        merke = "  [OPPHEVET — skal ikke brukes]" if r["opphevet"] else ""
        linjer.append(f"  {r['paragraf']} — {r['overskrift']}{merke}")

    return "<lovregister>\n" + "\n".join(linjer) + "\n</lovregister>"
