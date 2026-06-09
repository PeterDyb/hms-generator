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
Harvey (JSON, validert) → Donna (JSON-plan, validert) → Mike (per kapittel + kvalitetsport)
  → KODE setter sammen dokumentene (forside, TOC, endringslogg — deterministisk)
  → kvalitetsport i kode (plassholdere, kapitteldekning, hjemmelskontroll)
  → Louis QA (maks 1 reparasjonsrunde via Mike) → Jessica endelig verifisering → leveranse
```

Sentrale garantier i `pipeline.py`:
- `stop_reason == "max_tokens"` ⇒ hard feil — aldri levere avkuttede dokumenter
- All agent-JSON valideres med retry (2 forsøk) før neste steg
- `temperature = 0.2` — compliance-dokumenter skal være deterministiske
- Brukerfelter sendes som avgrenset data (`<bedriftsinformasjon>`) — aldri som instruksjoner

## Stack

- **Claude API** (Anthropic) — alle agenter kjører på `claude-sonnet-4-6`
- **Supabase** — sesjoner, agent-kjøringer, håndbøker, NACE-krav.
  Backend bruker `service_role`-nøkkelen; anon har KUN lesetilgang til `harvey_nace_krav`.
- **FastAPI** — API med nøkkel-auth, rate limiting og sikkerhetsheadere (CSP uten inline-script)

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
├── README.md          # arkitekturoversikt
├── AGENTREVIEW.md     # agent-/kvalitetsreview med målbilde
├── server.py          # FastAPI-server
├── pipeline.py        # agent-pipeline med kvalitetsporter + dokumentgeneratorer
├── agents/            # agentdefinisjoner (personlighet + ansvar)
├── prompts/           # system-prompter som sendes til Claude API
├── ui/                # frontend (index.html + app.js — ingen inline-script)
└── output/            # genererte håndbøker (ignoreres av git)
```
