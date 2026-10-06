# HMS-generator — prosjektguide for Claude

## Prosjektbeskrivelse

AI-drevet generator for HMS-håndbøker og personalhåndbøker skreddersydd
for norske bedrifter. Systemet bruker et team av spesialiserte agenter
som samarbeider i en pipeline med kvalitetsporter i kode: fra lovkartlegging
til kvalitetskontrollert, godkjent dokument.

## Agentteamet

| Agent | Fil | Ansvar |
|---|---|---|
| Harvey | `agents/harvey.md` | Lovverk — kartlegger alle gjeldende krav (strukturert JSON) |
| Donna | `agents/donna.md` | Kapittelplan — strukturert JSON-plan fra Harveys lovliste |
| Mike | `agents/mike.md` | Kapittelinnhold — skriver ETT kapittel per API-kall |
| Louis | `agents/louis.md` | Kvalitetskontroll — funnliste per dokument; funn sendes tilbake til Mike (maks én reparasjonsrunde) |
| Jessica | `agents/jessica.md` | Endelig verifisering — godkjenner kun når Harveys lovliste er dekket |
| Rex | `agents/rex.md` | Sikkerhet — fullstendig sikkerhetsanalyse av systemet |

## Pipeline-arkitektur

```
Harvey (JSON, validert) → Donna (JSON-plan, validert + dekningsport)
  → Mike (ett kall per kapittel, 6 parallelt, kvalitetsport per kapittel)
  → KODE setter sammen dokumentene (forside, TOC, endringslogg — deterministisk)
  → kvalitetsport + faktaport i kode
  → Louis QA (maks 1 reparasjonsrunde, kun kapitler med funn)
  → Jessica endelig verifisering (dekning + konsistens på tvers) → leveranse
```

Sentrale garantier i `pipeline.py`:
- `stop_reason == "max_tokens"` ⇒ hard feil — aldri levere avkuttede dokumenter
- All agent-JSON valideres med retry (2 forsøk) før neste steg
- Ingen `temperature` — Sonnet 5 tar ikke parameteren (400). Determinismen ligger
  i kvalitetsportene, ikke i sampling-innstillinger
- Brukerfelter sendes som avgrenset data (`<bedriftsinformasjon>`) — aldri som instruksjoner
- Mikes kapitler samles i PLANENS rekkefølge, aldri i fullføringsrekkefølge —
  parallell skriving må gi identisk dokument hver gang
- Kun `KRITISK`/`HØY` fra Louis stopper leveransen; `MIDDELS` rettes uten å blokkere
- Nettverksfeil prøves om igjen (4 forsøk); endelige feil bobler opp med én gang

## Stack

- **Claude API** (Anthropic) — alle agenter kjører på `claude-sonnet-5` med adaptiv thinking
- **Supabase** — sesjoner, agent-kjøringer, håndbøker, NACE-krav.
  Backend bruker `service_role`-nøkkelen; anon har KUN lesetilgang til `harvey_nace_krav`.
- **FastAPI** — API med nøkkel-auth, rate limiting og sikkerhetsheadere (CSP uten inline-script)

## Hvor hører en endring hjemme

| | Hva | Hvorfor |
|---|---|---|
| **Supabase** | Alt som er sant i verden og kan endre seg — lovhjemler, forskrifter, bransjekrav | Kan verifiseres, dateres og oppdateres uten kodeendring |
| **Kode** | Regler som ikke skal kunne overtales — porter, faktaregister, datosjekk | Deterministisk og testbart |
| **Prompt** | Bare *hvordan* det skrives — tone, struktur, disposisjon | Aldri hva som er sant |

En lovregel skrevet inn i en prompt eldes stille. Samme regel i
`nace_forskriftskrav` har `verifisert_dato` og kan revideres. Se `ARKITEKTUR.md`.

## Viktige regler

- Referer **alltid** til Arbeidsmiljøloven (AML) med korrekte paragrafhenvisninger
- Referer **alltid** til Internkontrollforskriften (IK-forskriften, FOR-1996-12-06-1127)
- Lovterskler per 2024: verneombud fra **5** ansatte, AMU fra **30**, varsling i **kap. 2A**,
  OTP fra **første krone**, feriepenger 60+ er **12,5 %**
- Ingen håndbøker leveres uten at Louis har godkjent og Jessica har verifisert Harveys lovliste
- All kode og dokumentasjon skrives på **norsk bokmål**
- Hemmeligheter ligger kun i `.env` (aldri i kode, aldri i frontend, aldri i git)

## Mappestruktur

```
hms-generator/
├── CLAUDE.md          # denne filen
├── README.md          # oversikt og kom i gang
├── ARKITEKTUR.md      # hvordan systemet henger sammen og hvorfor
├── AGENTREVIEW.md     # agent-/kvalitetsreview med målbilde
├── JURISTGJENNOMGANG.md # lovpåstander kontrollert mot Lovdata + åpne spørsmål
├── server.py          # FastAPI-server
├── pipeline.py        # agent-pipeline med kvalitetsporter + dokumentgeneratorer
├── agents/            # agentdefinisjoner (personlighet + ansvar)
├── prompts/           # system-prompter som sendes til Claude API
├── tests/             # pytest (uten nett); HMS_INTEGRASJON=1 for Supabase-testene
├── ui/                # frontend (index.html + app.js — ingen inline-script)
└── output/            # genererte håndbøker (ignoreres av git)
```
