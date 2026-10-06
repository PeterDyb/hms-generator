"""
NACE-basert kravmotor.

Kjeden er: organisasjonsnummer → Brønnøysund → NACE-kode → bransjekrav med
konkrete forskriftshjemler, som Harvey siterer i stedet for generisk tekst.

Merk om kodeformat: Brønnøysund oppgir NACE etter SN2007 med fem siffer og
punktum — «41.200», «86.211». Oppslagstabellen MÅ bruke samme format, ellers
treffer aldri oppslaget. (Tabellen inneholder også eldre rader på formen «F41»
og «Q86». De er ikke søkbare fra et Brreg-oppslag og regnes som utgåtte.)
"""
from __future__ import annotations

import brreg

# Når en NACE-kode ikke er dekket, sier vi det rett ut i stedet for å gjette.
# Harvey får da beskjed om å behandle bransjekravene som uavklarte.
DEKNING_FULL = "full"
DEKNING_INGEN = "ingen"


def _rad_til_bransje(rad: dict, hjemler: list[dict]) -> dict:
    """Bygg svaret Harvey får. bht_paakrevd er tri-state — None betyr uavklart."""
    bht = rad.get("bht_paakrevd")
    return {
        "nace_kode": rad.get("nace_kode", ""),
        "nace_navn": rad.get("nace_navn", ""),
        "nace_hovedgruppe": rad.get("nace_hovedgruppe", ""),
        "risikonivaa": rad.get("risikonivaa"),
        "bht_paakrevd": bht,
        # Skiller «nei, ikke påkrevd» fra «ingen har sjekket det».
        "bht_maa_vurderes": bht is None,
        "dokumentkrav": list(rad.get("dokumentkrav") or []),
        "forskriftskrav": hjemler,
        "dekning": DEKNING_FULL,
    }


def udekket(nace_kode: str, nace_navn: str = "") -> dict:
    """Svar for en NACE-kode vi ikke har seedet krav for."""
    return {
        "nace_kode": nace_kode,
        "nace_navn": nace_navn,
        "nace_hovedgruppe": "",
        "risikonivaa": None,
        "bht_paakrevd": None,
        "bht_maa_vurderes": True,
        "dokumentkrav": [],
        "forskriftskrav": [],
        "dekning": DEKNING_INGEN,
    }


def hent_bransjekrav(nace_kode: str, supabase) -> dict:
    """
    Slå opp bransje + forskriftshjemler for én NACE-kode.

    Returnerer alltid et svar. Er koden ikke dekket, har svaret
    dekning == "ingen" og tom forskriftsliste — aldri oppdiktede hjemler.
    """
    if not nace_kode:
        return udekket("")

    try:
        rader = (
            supabase.table("harvey_nace_krav")
            .select("*")
            .eq("nace_kode", nace_kode)
            .limit(1)
            .execute()
        ).data or []
    except Exception:
        return udekket(nace_kode)

    if not rader:
        return udekket(nace_kode)

    try:
        hjemler = (
            supabase.table("nace_forskriftskrav")
            .select("forskrift_navn, forskrift_nummer, paragraf, krav, "
                    "dokumenttype, kilde_url, verifisert_dato")
            .eq("nace_kode", nace_kode)
            .order("forskrift_nummer")
            .execute()
        ).data or []
    except Exception:
        hjemler = []

    return _rad_til_bransje(rader[0], hjemler)


def krav_for_orgnr(orgnr: str | int, supabase, klient=None) -> dict:
    """
    Hele kjeden: organisasjonsnummer inn, bransjekrav ut.

    Returnerer {"enhet": ..., "bransje": ..., "sekundaerbransjer": [...]}.
    Kaster brreg.BrregFeil hvis oppslaget mot Enhetsregisteret feiler —
    kalleren avgjør om det skal gi feilmelding eller manuell utfylling.
    """
    enhet = brreg.slaa_opp_enhet(orgnr, klient=klient)
    koder = enhet["naeringskoder"]
    if not koder:
        return {"enhet": enhet, "bransje": udekket(""), "sekundaerbransjer": []}

    hoved = hent_bransjekrav(koder[0]["kode"], supabase)
    if hoved["dekning"] == DEKNING_INGEN and not hoved["nace_navn"]:
        # Bruk Brregs egen beskrivelse så dokumentet iallfall navngir bransjen.
        hoved["nace_navn"] = koder[0].get("beskrivelse", "")

    # naeringskode2/3 tas med når de finnes — en bedrift kan drive både
    # verksted og butikk, og da gjelder kravene fra begge.
    sekundaere = []
    for k in koder[1:]:
        krav = hent_bransjekrav(k["kode"], supabase)
        if krav["dekning"] == DEKNING_INGEN and not krav["nace_navn"]:
            krav["nace_navn"] = k.get("beskrivelse", "")
        sekundaere.append(krav)

    return {"enhet": enhet, "bransje": hoved, "sekundaerbransjer": sekundaere}


def til_promptblokk(bransje: dict, sekundaerbransjer: list[dict] | None = None) -> str:
    """
    Formater kravene som avgrenset data til Harvey.

    Skrives som data, ikke som instruksjoner — samme prinsipp som
    <bedriftsinformasjon> ellers i pipelinen.
    """
    sekundaerbransjer = sekundaerbransjer or []

    def blokk(b: dict, tittel: str) -> list[str]:
        ut = [f"{tittel}: {b['nace_kode']} {b['nace_navn']}".rstrip()]
        if b["risikonivaa"]:
            ut.append(f"Risikonivå: {b['risikonivaa']}")
        if b["dekning"] == DEKNING_INGEN:
            ut.append(
                "Dekning: INGEN verifiserte bransjekrav i databasen for denne koden. "
                "Ikke oppgi bransjeforskrifter du ikke har hjemmel for — sett i stedet "
                "krever_manuell_vurdering=true på de bransjespesifikke kravene."
            )
            return ut
        if b["bht_maa_vurderes"]:
            ut.append(
                "BHT: uavklart for denne bransjen. Sett bht_paakrevd=false og legg inn "
                "et bransjespesifikt krav med krever_manuell_vurdering=true som ber "
                "bedriften sjekke FOR-2011-12-06-1355 § 13-1."
            )
        else:
            ut.append(f"BHT-plikt: {'ja' if b['bht_paakrevd'] else 'nei'} "
                      f"(vurdert mot FOR-2011-12-06-1355 § 13-1)")
        if b["dokumentkrav"]:
            ut.append("Dokumenter bransjen må ha utover IK-forskriften § 5: "
                      + "; ".join(b["dokumentkrav"]))
        # Skill hjemler som er kontrollert mot kilden fra hjemler som ennå ikke
        # er det. Uten dette skillet ble ALT presentert som «verifisert», og en
        # ukontrollert paragrafhenvisning ble sitert som fasit — nøyaktig den
        # feilen som ga «§ 2A-3» for ekstern varsling og «hvert 3. år» for
        # FSE-førstehjelp.
        verifiserte = [f for f in b["forskriftskrav"] if f.get("verifisert_dato")]
        ukontrollerte = [f for f in b["forskriftskrav"] if not f.get("verifisert_dato")]

        if verifiserte:
            ut.append("Verifiserte hjemler — bruk NØYAKTIG disse henvisningene:")
            for f in verifiserte:
                ut.append(
                    f"  - {f['forskrift_navn']} ({f['forskrift_nummer']}) {f['paragraf']}: "
                    f"{f['krav']}"
                )

        if ukontrollerte:
            ut.append(
                "Krav som GJELDER bransjen, men der paragrafnummeret ikke er "
                "kontrollert mot kilden. Temaet SKAL dekkes i håndboken. Vis til "
                "forskriften ved navn og nummer — ikke oppgi paragrafnummer for "
                "disse, og ikke gjett på frekvenser eller terskelverdier som ikke "
                "står i kravteksten:"
            )
            for f in ukontrollerte:
                ut.append(
                    f"  - {f['forskrift_navn']} ({f['forskrift_nummer']}): {f['krav']}"
                )
        return ut

    linjer = blokk(bransje, "Hovedbransje")
    for i, s in enumerate(sekundaerbransjer, start=2):
        linjer.append("")
        linjer.extend(blokk(s, f"Tilleggsbransje {i}"))
    return "<bransjekrav>\n" + "\n".join(linjer) + "\n</bransjekrav>"
