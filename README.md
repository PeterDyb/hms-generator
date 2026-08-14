# HMS-generator

Automatisk generering av HMS-håndbøker og personalhåndbøker for norske bedrifter,
med kvalitetsporter som garanterer komplette dokumenter — eller ingen leveranse.

## Oversikt

```
Brukerinput (skjema)
    │
    ▼
┌──────────────┐   strukturert JSON (validert, retry)
│ Harvey ⚖️    │   Lovkartlegging: AML, IK-forskriften, NACE-krav, flagg
└──────┬───────┘
       ▼
┌──────────────┐   strukturert kapittelplan (JSON, validert)
│ Donna 📋     │   Innholdsplan for HMS- og personalhåndbok
└──────┬───────┘
       ▼
┌──────────────┐   ETT API-kall per kapittel + kvalitetsport per kapittel
│ Mike ✍️      │   Skriver ferdig tekst (lengde, plassholdere, overskrift sjekkes)
└──────┬───────┘
       ▼
┌──────────────┐   Deterministisk: forside, innholdsfortegnelse, endringslogg
│ KODE 🔧      │   + kvalitetsport: kapitteldekning, plassholdere, hjemmelskontroll
└──────┬───────┘
       ▼
┌──────────────┐   Strukturert funnliste; funn → Mike skriver om (maks 1 runde)
│ Louis 🔍     │   Kvalitetskontroll: lovsatser, hallusinerte hjemler, mangler
└──────┬───────┘
       ▼
┌──────────────┐   Godkjenner kun når Harveys lovliste er dekket
│ Jessica 👔   │   Endelig verifisering — ellers stoppes leveransen
└──────┬───────┘
       ▼
HMS-håndbok + personalhåndbok (Markdown) + risikovurdering (Excel) + 7 skjemaer (Word)
```

Feiler et kvalitetskrav, stopper pipelinen med tydelig feilmelding —
det leveres aldri ufullstendige eller avkuttede dokumenter.

## Kom i gang

1. `pip install -r requirements.txt`
2. Kopier `.env` og fyll inn nøkler (se kommentarene i filen):
   `ANTHROPIC_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `API_KEY`
3. Start: `uvicorn server:app --reload`
4. Åpne http://localhost:8000, oppgi tilgangsnøkkelen (`API_KEY`) og fyll inn bedriftsskjemaet
5. `MOCK_MODE=true` i `.env` kjører hele pipelinen uten API-kostnader

## Sikkerhet

- Alle `/api/`-endepunkter krever `X-API-Key`; nøkkelen oppgis av brukeren i UI-et
  og er aldri innbakt i HTML
- Backend bruker Supabase `service_role`; anon-rollen har kun lesetilgang til NACE-tabellen
- CSP uten inline-script; all markdown saneres med DOMPurify før rendering
- Brukerfelter sendes som avgrenset data til modellene — aldri som instruksjoner
- Rate limiting på alle endepunkter (slowapi)

## Regelverksgrunnlag (oppdatert per 2024-endringene)

- **Arbeidsmiljøloven** (AML, 2005) — inkl. verneombud fra 5 ansatte (§ 6-1),
  AMU fra 30 (§ 7-1), varsling kap. 2A, arbeidsavtalekrav fra 1.7.2024 (§ 14-6)
- **Internkontrollforskriften** (IK-forskriften, 1996) — § 5 andre ledd nr. 1–8,
  der nr. 4–8 er de kravene som skal dokumenteres skriftlig
- **Ferieloven**, **OTP-loven** (fra første krone, 2022), **Folketrygdloven** kap. 8–9
- Arbeidstilsynets bransjeveiledninger via NACE-tabellen i Supabase

> **Merk:** Genererte dokumenter er utkast og beslutningsstøtte — de skal alltid
> gjennomgås og godkjennes av bedriftens ledelse før bruk.

## Mappestruktur

```
hms-generator/
├── CLAUDE.md          # Prosjektguide for Claude
├── README.md          # Denne filen
├── AGENTREVIEW.md     # Agent-/kvalitetsreview
├── server.py          # FastAPI-server
├── pipeline.py        # Agent-pipeline + dokumentgeneratorer
├── agents/            # Agentdefinisjoner (Harvey, Donna, Mike, Louis, Jessica, Rex)
├── prompts/           # System-prompter
├── ui/                # Frontend (index.html + app.js)
└── output/            # Genererte håndbøker (ignoreres av git)
```
