"""Hjemmelsregisteret: dataene i migreringene og porten som slår opp i dem."""
import re
from collections import Counter

import pytest

import lovregister


# ─── Dataene ────────────────────────────────────────────────────────────────


def test_ingen_paragraf_er_registrert_to_ganger(rader):
    nokler = Counter((r["lov_kortnavn"], lovregister._normaliser(r["paragraf"])) for r in rader)
    assert [n for n, antall in nokler.items() if antall > 1] == []


def test_alle_rader_er_verifisert_med_kilde(rader):
    for r in rader:
        assert r["verifisert_dato"], r
        assert r["kilde_url"].startswith("https://lovdata.no/"), r


@pytest.mark.parametrize("lov,antall", [
    ("AML", 197), ("IKF", 11), ("FERIEL", 18), ("OTPL", 11), ("LDL", 49),
])
def test_hele_lover_er_komplette(rader, lov, antall):
    """Lovene er lagt inn i sin helhet. Faller tallet, er en paragraf borte —
    og da melder porten en gyldig hjemmel som ikke-eksisterende."""
    assert sum(r["lov_kortnavn"] == lov for r in rader) == antall


def test_aml_kapitler_har_sammenhengende_nummerering(rader):
    """Et kapittel med hull i nummereringen er ikke komplett."""
    per_kap: dict[str, list[int]] = {}
    for r in rader:
        if r["lov_kortnavn"] != "AML":
            continue
        nr = lovregister._normaliser(r["paragraf"]).split("-")[1]
        if re.fullmatch(r"\d+", nr):
            per_kap.setdefault(r["kapittel"], []).append(int(nr))
    for kap, numre in per_kap.items():
        assert sorted(numre) == list(range(1, max(numre) + 1)), f"kapittel {kap}"


def test_aml_kapittel_15_lenker_til_riktig_lovdata_side(rader):
    """004 lenket kapittel 15 til KAPITTEL_16, som er kapittel 14 A."""
    urler = {r["kilde_url"] for r in rader if r["lov_kortnavn"] == "AML" and r["kapittel"] == "15"}
    assert urler == {"https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_17"}


@pytest.mark.parametrize("paragraf,overskrift", [
    ("§ 5-1", "Registrering av skader og sykdommer"),
    ("§ 5-2", "Arbeidsgivers varslings- og meldeplikt"),
    ("§ 2A-6", "Plikt til å utarbeide rutiner for intern varsling"),
    ("§ 2A-7", "Taushetsplikt ved ekstern varsling til offentlig myndighet"),
    ("§ 12-1", "Svangerskapskontroll"),
    ("§ 14-16", "Arbeidsreglement"),
    ("§ 14-17", "Fastsettelse av arbeidsreglement"),
])
def test_hjemler_som_tidligere_ble_husket_feil(register, paragraf, overskrift):
    rad = register["lover"]["AML"]["paragrafer"][lovregister._normaliser(paragraf)]
    assert rad["overskrift"] == overskrift


# ─── Gjenkjenning i tekst ───────────────────────────────────────────────────


@pytest.mark.parametrize("tekst,forventet", [
    ("jf. AML § 3-1", [("AML", "3-1")]),
    ("arbeidsmiljøloven § 2A-7", [("AML", "2A-7")]),
    ("arbeidsmiljølovens § 2 A-7", [("AML", "2A-7")]),
    ("AML §§ 2-1, 2-3 og 4-1", [("AML", "2-1"), ("AML", "2-3"), ("AML", "4-1")]),
    ("AML § 14-12 a gjelder", [("AML", "14-12A")]),
    ("AML § 15-13a.", [("AML", "15-13A")]),
    ("IK-forskriften § 5 andre ledd", [("IKF", "5")]),
    ("IK-forskriften § 5 i praksis", [("IKF", "5")]),
    ("internkontrollforskriften § 4", [("IKF", "4")]),
    ("Ftrl. § 8-24", [("FTRL", "8-24")]),
    ("folketrygdloven § 9-6", [("FTRL", "9-6")]),
    ("ferieloven § 10 første ledd", [("FERIEL", "10")]),
    ("likestillings- og diskrimineringsloven § 26a", [("LDL", "26A")]),
    ("OTP-loven § 4", [("OTPL", "4")]),
    ("§ 5-2 uten lovnavn", []),
    ("samlet § 3-1", []),
])
def test_siterte_paragrafer(tekst, forventet):
    assert lovregister.siterte_paragrafer(tekst) == forventet


# ─── Porten ─────────────────────────────────────────────────────────────────


def test_louis_feilen_gjentas_ikke(register):
    """Louis kalte både § 5-1 og § 2A-7 feil i hver sin runde. Begge er gyldige."""
    tekst = ("Meldeplikt etter AML § 5-2. Registrering etter AML § 5-1. "
             "Taushetsplikt ved ekstern varsling, AML § 2A-7.")
    assert lovregister.hjemmelsfeil(tekst, register) == []


def test_ikke_eksisterende_paragraf_i_komplett_kapittel(register):
    feil = lovregister.hjemmelsfeil("AML § 2A-9", register)
    assert len(feil) == 1 and "2A-9 finnes ikke" in feil[0]


def test_kapittel_14_kontrolleres_naa(register):
    assert lovregister.hjemmelsfeil("AML § 14-6", register) == []
    assert "finnes ikke" in lovregister.hjemmelsfeil("AML § 14-21", register)[0]


def test_opphevet_paragraf_meldes(register):
    feil = lovregister.hjemmelsfeil("jf. AML § 2-4", register)
    assert len(feil) == 1 and "OPPHEVET" in feil[0]


def test_flat_lov_kontrolleres_i_sin_helhet(register):
    assert lovregister.hjemmelsfeil("IK-forskriften § 5", register) == []
    feil = lovregister.hjemmelsfeil("IK-forskriften § 12", register)
    assert len(feil) == 1 and "loven er kontrollert" in feil[0]


def test_ftrl_kapittel_utenfor_registeret_sies_ingenting_om(register):
    """Bare kapittel 8 og 9 er registrert. Et gjett om kapittel 14 ville vært
    samme feil som den registeret skal rette."""
    assert lovregister.hjemmelsfeil("folketrygdloven § 14-7", register) == []
    assert lovregister.hjemmelsfeil("ftrl. § 8-99", register) != []


def test_paragraf_uten_lovnavn_kontrolleres_ikke(register):
    assert lovregister.hjemmelsfeil("§ 99-99", register) == []


def test_tomt_register_melder_ingenting():
    assert lovregister.hjemmelsfeil("AML § 99-1", {"lover": {}}) == []


def test_samme_feil_meldes_en_gang(register):
    assert len(lovregister.hjemmelsfeil("AML § 2A-9 og AML § 2A-9", register)) == 1


def test_promptblokk_utelater_opphevede_og_er_sortert(register):
    blokk = lovregister.til_promptblokk(register)
    assert blokk.startswith("<lovregister>") and blokk.endswith("</lovregister>")
    assert "§ 2-4 —" not in blokk
    assert blokk.index("§ 2-3 —") < blokk.index("§ 2A-1 —") < blokk.index("§ 3-1 —")
    assert blokk.index("§ 14-20 —") < blokk.index("§ 14A-1 —") < blokk.index("§ 15-1 —")
    assert blokk.index("§ 9-1 —") < blokk.index("§ 10-1 —")


def test_databasen_er_lik_migreringene(supabase, rader):
    """Integrasjon: det pipelinen slår opp i er det migreringene beskriver."""
    db = supabase.table("lovhjemler").select(
        "lov_kortnavn, paragraf, overskrift, opphevet").execute().data
    som_sett = lambda rr: {(r["lov_kortnavn"], r["paragraf"], r["overskrift"], r["opphevet"])
                           for r in rr}
    assert som_sett(db) == som_sett(rader)
