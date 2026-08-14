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
┌──────────────┐   Deterministisk: forside, innholdsfortegnelse, endringslogg,
│ KODE 🔧      │   vedleggsoversikt + kvalitetsport (se «Kvalitetsporter»)
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
HMS-håndbok + personalhåndbok + risikovurdering + årlig revisjonsskjema + 7 skjemaer
```

Feiler et kvalitetskrav, stopper pipelinen med tydelig feilmelding —
det leveres aldri ufullstendige eller avkuttede dokumenter.

## Leveranse

Alt havner i `output/<session_id>/`, prefikset med bedriftsnavn og dato.

| Dokument | Formater | Hjemmel / formål |
|---|---|---|
| HMS-håndbok | `md`, `json`, `docx`, `pdf` | IK-forskriften § 5 andre ledd nr. 4–8 |
| Personalhåndbok | `md`, `json`, `docx`, `pdf` | AML kap. 2A, 14, ferieloven, OTP |
| Risikovurdering | `xlsx`, `json`, `docx`, `pdf` | IK-forskriften § 5 andre ledd nr. 6 |
| Årlig gjennomgang av HMS-systemet | `docx`, `pdf` | IK-forskriften § 5 andre ledd nr. 8 |
| 7 utfyllbare skjemaer | `docx` | AML § 3-1, § 3-4, § 14-5, ftrl. § 8-24, GDPR |

**JSON-formatet** er maskinlesbart med dokumentmeta, kapitler og hjemler — laget
for videre integrasjon (kundeportal, avvikssystem, arkiv).

De sju skjemaene: avviksmelding, sjekkliste vernerunde, handlingsplan HMS,
oppfølgingsplan sykefravær (HMS) — arbeidsavtale, egenmeldingsskjema,
taushetserklæring (personal). Skjemaene er ikke løse filer på en disk: håndboken
får et eget **vedleggskapittel** som viser hvert skjema med bruksområde, filnavn
og hjemmel, slik at dokumentasjonen henger sammen ved tilsyn.

## Kvalitetsporter

Portene er kode, ikke modellvurderinger — de kan ikke overtales bort.

**Per kapittel** (alt Mike skriver): riktig overskrift, minstelengde,
ingen gjenglemte plassholdere.

**Per sammensatt dokument** (både HMS- og personalhåndbok):
- Alle planlagte kapitler finnes i dokumentet
- Ingen plassholdere noe sted

**Kun HMS-håndboken:**
- **Målbare HMS-mål** — minst 3 mål i tabell (Mål | Måltall | Frist | Ansvarlig),
  der måltall og frist må inneholde tall (IK-forskriften § 5 andre ledd nr. 4)
- **IK-dekning** — hvert av kravene nr. 4–8 må ha et *eget* kapittel, med treff
  både i overskrift og innhold, så generell standardtekst ikke kan «dekke» et
  krav som mangler

**Hjemmelskontroll:** koden finner §-referanser i dokumentet som ikke kan spores
til Harveys lovliste eller kjent-listen, og sender dem inn i Louis' kontroll som
flagg — Louis avgjør om de er hallusinerte eller legitime.

**Hard feil:** `stop_reason == "max_tokens"` fra modellen avbryter kjøringen.
Et avkuttet compliance-dokument er verre enn ingen leveranse.

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
├── pipeline.py        # Agent-pipeline, kvalitetsporter, Excel + Word-skjemaer
├── eksport.py         # Eksportlag: JSON/DOCX/PDF, HMS-mål- og IK-kontroll
├── agents/            # Agentdefinisjoner (Harvey, Donna, Mike, Louis, Jessica, Rex)
├── prompts/           # System-prompter
├── ui/                # Frontend (index.html + app.js)
└── output/            # Genererte håndbøker (ignoreres av git)
```
