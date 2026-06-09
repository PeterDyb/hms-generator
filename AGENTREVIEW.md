# Agentreview — Harvey, Donna, Mike, Jessica

**Dato:** 09.06.2026
**Mål:** Identifisere hvorfor genereringen ikke leverer 100 % komplette håndbøker hver gang, og hva som må endres for å garantere det.

---

## Hovedkonklusjon

Promptene er gode på tone og struktur, men arkitekturen gjør komplett leveranse umulig i praksis. Tre rotårsaker:

1. **`max_tokens=4096` for alle agenter** (`pipeline.py`, `_stream_real`). Mike skal skrive 13 HMS-kapitler + 14 personalkapitler, og Jessica skal levere *begge ferdige håndbøker* i ett svar. 4096 tokens er ca. 8–10 sider — dokumentene kuttes garantert. I tillegg sjekkes aldri `stop_reason`: et avkuttet svar markeres «completed» og leveres til kunden.
2. **Jessica er en «kopist»**. Hun bes reprodusere alt Mike skrev «uten at noe kuttes» — det er nøyaktig situasjonen der språkmodeller komprimerer og sammenfatter. Sammenstilling (forside, innholdsfortegnelse, endringslogg, rekkefølge) er deterministisk arbeid som bør gjøres i kode, ikke av en LLM.
3. **Ingen programmatisk validering eller retry.** Jessicas sluttkontroll-sjekkliste er kun tekst i en prompt — ingenting i koden verifiserer den. `_extract_harvey_json` som returnerer `None` tolereres stille (alle flagg blir `false`), og splitting på strengen `=== PERSONALHÅNDBOK ===` betyr at hele personalhåndboken forsvinner lydløst hvis Jessica formaterer markøren litt annerledes.

---

## Funn per agent

### Harvey (lovkartlegging)

| ID | Funn | Fix |
|---|---|---|
| H-1 | «Du er aldri usikker» inviterer til hallusinering av hjemler | Snu instruksen: bruk kun NACE-data og lovtabellen i prompten; ukjente tilfeller merkes `"krever_manuell_vurdering": true` |
| H-2 | JSON leveres som fritekst og parses med regex | Bruk Anthropic tool use / structured outputs med JSON-skjema; valider med Pydantic; retry med feilmelding ved ugyldig JSON |
| H-3 | Varsling henvises til § 2-4/§ 2-5 — flyttet til **kap. 2A (§ 2A-1 ff.)** i 2017 | Oppdater lovtabellen |
| H-4 | OTP «minimum 2 % av lønn mellom 1G og 12G» — utdatert; fra 2022 gjelder opptjening **fra første krone** (0–12G), aldersgrense 13 år, ingen 20 %-stillingsgrense | Oppdater |
| H-5 | Verneombud «10 eller flere» og AMU 50 — utdatert (5 og 30 fra 1.1.2024) | Oppdater (også flagget i hovedrapporten) |
| H-6 | Inkonsekvent feltnavn: prompt-eksempel bruker `gjelder_naar`, mock bruker begge varianter, Excel-koden leser `gjelder_når` → data faller bort | Standardiser på ett feltnavn i skjemaet |

### Donna (innholdsplan)

| ID | Funn | Fix |
|---|---|---|
| D-1 | Output er fritekst-markdown — Mike og koden har ingen kontrakt å validere mot | La Donna returnere strukturert JSON (kapittelliste med tittel, formål, stikkord, hjemler). Da kan koden sjekke at *hvert* kapittel faktisk blir skrevet |
| D-2 | Kap. 2: «AMU … kun med hvis `bht_paakrevd` eller `amu_paakrevd`» — BHT-flagget skal ikke styre AMU-kapitlet | Rydd i logikken: BHT-kapittel ved `bht_paakrevd`, AMU-kapittel ved `amu_paakrevd` |
| D-3 | Risikovurdering «minimum hvert 2. år» — Mike/mock sier årlig. Intern motsigelse | Velg én standard (anbefalt: årlig + ved endringer) |
| D-4 | Lovfeil som arves nedover: verneombud 10 (→5), AMU 50 (→30), feriepenger 60+ 12 % (→12,5 %), omsorgsdager 20 ved 3+ barn (→15), varsling § 2-4/§ 2-5 (→§ 2A), «14 obligatoriske punkter» i § 14-6 (flere fra 1.7.2024), utvidet egenmelding presentert som standard | Rett alle; dette er samme feilfamilie som i hovedrapporten |

### Mike (kapittelinnhold)

| ID | Funn | Fix |
|---|---|---|
| M-1 | Ett kall skal produsere ~27 kapitler «klare til trykk» — kvaliteten faller mot slutten av lange svar, og 4096 tokens kutter lenge før det | **Generer per kapittel**: ett API-kall per kapittel fra Donnas strukturerte plan. Gir jevn kvalitet, kan parallelliseres, og feilede kapitler kan kjøres på nytt isolert |
| M-2 | Mike får **ikke** Harveys analyse (`run_mike` sender kun Donnas plan + bedriftsinfo) — risikofaktorer og hjemler må overleve via Donnas prosa | Send Harvey-JSON til Mike også |
| M-3 | Tallfeil i prompten: feriepenger 60+ «12,0 %» (→12,5 %), OTP 1G–12G + 20 %-regel (utdatert), pause «30 min ved over 5,5 t» (30 min gjelder først ved 8 t; over 5,5 t gir rett til *én pause*), varsling § 2-4/§ 2-5 (→§ 2A), verneombud-eksempel «10 eller flere» (→5) | Rett |
| M-4 | «Bruk bedriftens faktiske navn overalt» — men bedriftsnavnet er HTML-escapet før det når prompten (f.eks. `&amp;` i «Bygg & Bo AS») | Escape ved *rendering*, ikke ved lagring/prompting |

### Jessica (sammenstilling og QA)

| ID | Funn | Fix |
|---|---|---|
| J-1 | Skal reprodusere to komplette håndbøker i ett svar på 4096 tokens — hovedårsaken til ufullstendige leveranser | Fjern reproduksjonsjobben helt (se målbilde under) |
| J-2 | `=== PERSONALHÅNDBOK ===`-splitting er skjør; ved avvik forsvinner personalhåndboken stille | To separate kall, eller sammenstilling i kode |
| J-3 | Sjekklisten håndheves ikke — «aldri lever ufullstendig» er bare en oppfordring | Implementer sjekklisten som kode (se kvalitetsporter) |
| J-4 | Egne tallfeil: feriepenger «12 % for 60+», OTP «min. 20 % stilling, over 20 år» | Rett |

---

## Målbilde: pipeline som leverer 100 % hver gang

```
Harvey  → tool-use JSON (skjemavalidert, temp 0, retry ×2)
Donna   → strukturert kapittelplan (JSON, skjemavalidert)
Mike    → ETT KALL PER KAPITTEL (parallelt, retry per kapittel)
Kode    → setter sammen: forside + TOC + kapitler + endringslogg (deterministisk)
Jessica → QA-pass: leser ferdig dokument, returnerer strukturert funnliste
Kode    → regenererer kun kapitler med funn (maks 2 iterasjoner) → lever
```

**Kvalitetsporter i kode (kjøres før noe markeres «completed»):**

1. `stop_reason != "max_tokens"` på alle kall — ellers automatisk fortsettelse eller hard feil
2. Alle kapitler i Donnas plan finnes i sluttdokumentet (tittel-matching)
3. Plassholder-regex: ingen `[fyll inn]`, `TBD`, `XXX`, `[dato]` (unntakene fra Jessicas liste)
4. Hjemmelskontroll: alle §-referanser i dokumentet finnes i Harveys lovliste eller en vedlikeholdt whitelist — fanger hallusinerte paragrafer
5. Minimumslengde per kapittel (f.eks. 150 ord) og totaldokument
6. Begge dokumenter til stede hvis personalhåndbok er bestilt
7. IK-forskriften § 5 a–e: nøkkelord-sjekk for at alle fem punkter er dekket

**Parametre:** `temperature=0.2` for alle agenter (compliance-dokumenter skal være deterministiske), `max_tokens` per agent (Harvey 4k, Donna 8k, Mike 4–8k *per kapittel*, Jessica 8k for QA-funn).

---

## Andre forbedringer observert

- **Mock-modus avviker fra ekte modus** i både format og feltnavn — tester mot mock beviser ingenting om prod. Lag én felles outputkontrakt og la mock bruke samme valideringskode.
- **Mock-streaming sover 80 ms per 60 tegn** — en full generering i mock tar minutter uten grunn. Reduser/dropp ved test.
- **`run_donna` defaulter flagg til `false`** når Harvey-JSON ikke kan parses — feil skal stoppe pipeline, ikke generere en håndbok uten AMU/BHT-kapitler i stillhet.
- **Ingen kostnadskontroll per kjøring** — logg tokens per agent per sesjon (finnes i API-responsen) for pris- og marginberegning.
- **README beskriver et annet agentsystem** (collector/analyzer/writer) — oppdater til Harvey/Donna/Mike/Jessica.
- **`.gitignore` bør utvides** med `.DS_Store` og `.claude/` før git init.
- **UI viser ikke feilårsak** ved `failed` — vis agentens feilmelding slik at kunden (eller support) ser hva som skjedde.
- **Excel-risikovurderingen** forhåndsutfyller «Risikonivå» fra Harvey, men lar Sannsynlighet/Konsekvens stå tomme — nivået bør enten beregnes av S×K eller S/K forhåndsutfylles fra alvorlighet, ikke begge deler halvveis.
- **Vernerunde-sjekklisten** er generisk for alle bransjer — generer kontrollpunktene fra Harveys risikofaktorer for ekte skreddersøm (sterkt salgsargument).

## Anbefalt rekkefølge

1. Fiks `max_tokens` + `stop_reason`-sjekk (én dags arbeid, fjerner den største feilkilden umiddelbart)
2. Flytt sammenstilling til kode + to separate Jessica-kall (fjerner splitting-skjørheten)
3. Innfør kvalitetsportene (plassholder, kapitteldekning, hjemmelskontroll)
4. Strukturert JSON for Harvey og Donna (tool use)
5. Per-kapittel-generering for Mike
6. Rett alle lov- og tallfeil i promptene (sammen med jurist-gjennomgangen fra hovedplanen, Fase 2)
