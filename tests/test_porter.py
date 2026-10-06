"""Kvalitetsportene og garantiene i pipeline.py — uten modell og uten database."""
import json
from types import SimpleNamespace

import pytest

import pipeline


@pytest.fixture(autouse=True)
def lovregister_fra_migreringene(register, monkeypatch):
    monkeypatch.setattr(pipeline, "_lovregister_cache", register)


KAP = {"nummer": 3, "tittel": "Verneombud"}
FYLL = " Verneombudet velges for to år og skal ivareta arbeidstakernes interesser." * 8


def _kapittel(tekst: str = "") -> str:
    return f"## 3. Verneombud\n\n{tekst}{FYLL}"


# ─── Kapittelporten ─────────────────────────────────────────────────────────


def test_godt_kapittel_passerer():
    assert pipeline._kapittelfeil(_kapittel("Jf. AML § 6-1."), KAP) == []


def test_manglende_overskrift():
    feil = pipeline._kapittelfeil("Tekst uten overskrift." + FYLL, KAP)
    assert any("Mangler overskriften" in f for f in feil)


def test_for_kort_kapittel():
    feil = pipeline._kapittelfeil("## 3. Verneombud\n\nKort.", KAP)
    assert any("For kort" in f for f in feil)


@pytest.mark.parametrize("plassholder", ["[fyll inn navn]", "TBD", "XXX", "[dato]"])
def test_plassholder_stopper(plassholder):
    feil = pipeline._kapittelfeil(_kapittel(f"Ansvarlig: {plassholder}."), KAP)
    assert any("Plassholder" in f for f in feil)


def test_kanoniske_plassholdere_er_lov():
    tekst = _kapittel("Lønn utbetales [Lønnsutbetalingsdato]. BHT: [Navn på BHT-leverandør].")
    assert pipeline._kapittelfeil(tekst, KAP) == []


def test_kapittelporten_slaar_opp_i_lovregisteret():
    feil = pipeline._kapittelfeil(_kapittel("Jf. AML § 6-9."), KAP)
    assert any("6-9 finnes ikke" in f for f in feil)


# ─── Faktaporten ────────────────────────────────────────────────────────────


def test_bedriftsnavn_med_annen_skrivemaate():
    feil = pipeline._faktafeil("Nordvest Elektro AS og NORDVEST ELEKTRO AS",
                               {"bedriftsnavn": "Nordvest Elektro AS"})
    assert len(feil) == 1 and "NORDVEST ELEKTRO AS" in feil[0]


def test_frist_i_fortiden():
    feil = pipeline._faktafeil("Frist 01.01.2020.", {"bedriftsnavn": "X AS"})
    assert any("Frist i fortiden" in f for f in feil)


def test_frist_i_framtiden_er_ok():
    assert pipeline._faktafeil("Frist 31.12.2099.", {"bedriftsnavn": "X AS"}) == []


# ─── Dokumentporten og sammenstilling ───────────────────────────────────────


def test_manglende_kapittel_i_dokumentet():
    feil = pipeline._kvalitetsfeil("## 1. Innledning\n\ntekst",
                                   [{"nummer": 1, "tittel": "Innledning"}, KAP])
    assert feil == ["Kapittel mangler i dokumentet: ## 3. Verneombud"]


def test_sammenstilling_folger_planens_rekkefolge():
    """Parallell skriving gir kapitlene i fullføringsrekkefølge. Dokumentet
    skal likevel være identisk hver gang."""
    k1 = ({"nummer": 1, "tittel": "A"}, "## 1. A\n\nførst")
    k2 = ({"nummer": 2, "tittel": "B"}, "## 2. B\n\nsist")
    info = {"bedriftsnavn": "Test AS", "antall_ansatte": 8}
    doc = pipeline._sett_sammen(info, "PERSONALHÅNDBOK", [k1, k2], "personal")
    assert doc.index("## 1. A") < doc.index("## 2. B")
    assert doc == pipeline._sett_sammen(info, "PERSONALHÅNDBOK", [k1, k2], "personal")
    assert doc.rstrip().endswith("| Første utgave | |")


# ─── Planporten ─────────────────────────────────────────────────────────────


def _plan(*titler):
    return {"hms_kapitler": [{"nummer": i + 1, "tittel": t} for i, t in enumerate(titler)],
            "personal_kapitler": [{"nummer": 1, "tittel": "Ansettelse"}]}


def test_varsling_kreves_naar_harvey_har_kartlagt_2a():
    harvey = {"lover_alltid_gjeldende": [{"paragrafer": ["§ 2A-1"]}]}
    assert pipeline._plan_mangler(_plan("Innledning"), harvey)
    assert pipeline._plan_mangler(_plan("Innledning", "Varsling"), harvey) == []


def test_arbeidsreglement_styres_av_flaggets_verdi():
    plan = _plan("Innledning")
    assert pipeline._plan_mangler(plan, {"arbeidsreglement_paakrevd": False}) == []
    assert pipeline._plan_mangler(plan, {"arbeidsreglement_paakrevd": True})


def test_plan_uten_personalkapitler_avvises_naar_den_er_bestilt():
    plan = {"hms_kapitler": [{"nummer": 1, "tittel": "A"}]}
    assert not pipeline._plan_ok(plan, {"oensker_personalhaandbok": True})
    assert pipeline._plan_ok(plan, {"oensker_personalhaandbok": False})


# ─── Louis ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("alvor,blokkerer", [
    ("KRITISK", True), ("HØY", True), ("høy", True), ("HIGH", True),
    ("MIDDELS", False), ("LAV", False), ("", False),
])
def test_bare_kritisk_og_hoy_blokkerer(alvor, blokkerer):
    assert bool(pipeline._blokkerende({"funn": [{"alvor": alvor}]})) is blokkerer


def test_registrerte_hjemler_sendes_ikke_til_louis_som_usporbare(register):
    doc = "AML § 14-8 a og AML § 14-9 og § 77-1"
    avvik = pipeline._hjemmel_avvik(doc, {}, register)
    assert avvik == ["§ 77-1"]


# ─── Modellkallet ───────────────────────────────────────────────────────────


class _FalskStrøm:
    def __init__(self, tekst, stop_reason):
        self.text_stream = iter([tekst])
        self._final = SimpleNamespace(stop_reason=stop_reason)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self._final


class _FalskKlient:
    def __init__(self, svar):
        self._svar = list(svar)
        self.kall = 0
        self.messages = self
        self.siste_kwargs = None

    def stream(self, **kwargs):
        self.kall += 1
        self.siste_kwargs = kwargs
        neste = self._svar.pop(0)
        if isinstance(neste, Exception):
            raise neste
        return neste


@pytest.fixture
def ekte_modus(monkeypatch):
    anthropic = pytest.importorskip("anthropic")
    monkeypatch.setattr(pipeline, "MOCK_MODE", False)
    monkeypatch.setattr(pipeline, "anthropic", anthropic, raising=False)
    monkeypatch.setattr(pipeline.time, "sleep", lambda s: None)


def test_max_tokens_er_hard_feil(ekte_modus, monkeypatch):
    klient = _FalskKlient([_FalskStrøm("avkuttet", "max_tokens")])
    monkeypatch.setattr(pipeline, "_anthropic", klient, raising=False)
    with pytest.raises(pipeline.PipelineError, match="avkuttet"):
        pipeline._kall_modell("mike", "system", "innhold")
    assert klient.kall == 1  # ikke prøvd om igjen


def test_ingen_temperature_sendes(ekte_modus, monkeypatch):
    klient = _FalskKlient([_FalskStrøm("ok", "end_turn")])
    monkeypatch.setattr(pipeline, "_anthropic", klient, raising=False)
    assert pipeline._kall_modell("mike", "system", "innhold") == "ok"
    assert "temperature" not in klient.siste_kwargs


def test_nettverksfeil_proves_om_igjen(ekte_modus, monkeypatch):
    klient = _FalskKlient([TimeoutError("read operation timed out"),
                           _FalskStrøm("ok", "end_turn")])
    monkeypatch.setattr(pipeline, "_anthropic", klient, raising=False)
    assert pipeline._kall_modell("mike", "system", "innhold") == "ok"
    assert klient.kall == 2


def test_nettverksfeil_gir_opp_etter_fire_forsok(ekte_modus, monkeypatch):
    klient = _FalskKlient([TimeoutError("timed out")] * 4)
    monkeypatch.setattr(pipeline, "_anthropic", klient, raising=False)
    with pytest.raises(pipeline.PipelineError, match="4 ganger"):
        pipeline._kall_modell("mike", "system", "innhold")


def test_endelig_feil_bobler_opp_med_en_gang(ekte_modus, monkeypatch):
    klient = _FalskKlient([ValueError("ugyldig forespørsel")])
    monkeypatch.setattr(pipeline, "_anthropic", klient, raising=False)
    with pytest.raises(ValueError):
        pipeline._kall_modell("mike", "system", "innhold")
    assert klient.kall == 1


# ─── JSON-uttrekk ───────────────────────────────────────────────────────────


def test_json_fra_kodeblokk_og_raatekst():
    data = {"godkjent": True}
    assert pipeline._extract_harvey_json(f"```json\n{json.dumps(data)}\n```") == data
    assert pipeline._extract_harvey_json(f"Her: {json.dumps(data)} ferdig") == data
    assert pipeline._extract_harvey_json("ingen json") is None
