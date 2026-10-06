# Arkitektur — HMS-generator

Denne filen forklarer hvordan systemet henger sammen og hvorfor det er bygget
slik. `README.md` er kom-i-gang-veiledningen; `CLAUDE.md` er arbeidsreglene.
Dette er systemforklaringen.

---

## 1. Hva systemet gjør

En norsk småbedrift fyller ut ett skjema. Ut kommer 23 filer: HMS-håndbok,
personalhåndbok, risikovurdering, innføringsplan, årlig revisjonsskjema og sju
utfyllbare skjemaer — i Markdown, PDF, Word, Excel og JSON.

Innholdet er tilpasset bedriftens bransje, størrelse og oppgitte risikoforhold,
og hvert dokument kontrolleres mot internkontrollforskriften før utlevering.

Den avgjørende designbeslutningen: **ingenting leveres hvis kvalitetskravene
ikke er oppfylt.** Et ufullstendig HMS-system er verre enn ingen leveranse,
fordi bedriften da tror de er i mål.

---

## 2. Datamodellen er fundamentet

Systemets kvalitet er en direkte funksjon av hvor godt Supabase-tabellene er
befolket. Dette er ikke en detalj — det er hovedinnsikten i hele prosjektet.

### Tabellene

| Tabell | Innhold |
|---|---|
| `sessions` | Én rad per generering: bedriftsopplysninger og status |
| `agent_runs` | Én rad per agentkjøring, med løpende output for live-visning |
| `handbooks` | Ferdige håndbøker i Markdown |
| `harvey_nace_krav` | Én rad per bransje: risikonivå, BHT-plikt, dokumentkrav |
| `nace_forskriftskrav` | **Én rad per paragraf**, med `kilde_url` og `verifisert_dato` |
| `lovhjemler` | Paragrafregister per lov — hele kapitler, kontrollert mot Lovdata |

### Hvorfor `verifisert_dato` er den viktigste kolonnen

En hjemmel uten dato er en hjemmel ingen har kontrollert. Kolonnen skiller to
tilstander som ellers ser like ut:

- **Verifisert** → Harvey får «bruk NØYAKTIG disse henvisningene»
- **Ukontrollert** → Harvey får «temaet SKAL dekkes, vis til forskriften ved navn
  og nummer — ikke oppgi paragrafnummer, og ikke gjett på frekvenser eller
  terskelverdier»

Skillet finnes fordi modellen dikter der dataene tier. To dokumenterte
eksempler fra første ekte leveranse:

- Tabellen kjente «arbeid i høyden, kapittel 17» uten terskel. Mike fylte hullet
  med en 2-metersgrense han kjente fra stillasregler. Den finnes ikke i
  forskriften — og en montør som leser det, dropper selen på 1,8 meter.
- FSE fantes ikke i tabellen i det hele tatt. Mike gjettet «repetisjon hvert 3.
  år» på førstehjelpsopplæring. Kravet er **årlig**.

Begge var ren dataknapphet, ikke modellfeil.

### Dekning i dag

**17 gjeldende bransjer.** Tabellen bar tidligere to kodeformater side om side:
gjeldende femsifrede SN2007-koder (`43.210`) og eldre koder med næringsbokstav
(`F43.21`). Kartleggingen viste et entydig mønster — de 17 femsifrede hadde
hjemler og dokumentkrav, de 28 bokstavkodene hadde ingen av delene.

De var dessuten usøkbare fra Brønnøysund, som oppgir SN2007. Kolonnen
`gjeldende` skjuler dem fra bransjevelgeren; radene beholdes fordi tidligere
sesjoner peker på dem via fremmednøkkel.

For `43.210` (elektro) ligger det nå ni hjemler: byggherreforskriften,
arbeid i høyden, sikkerhetsopplæring (verifisert) — pluss FEK, FSE, HMS-kort,
stoffkartotek, asbest og støy/vibrasjon (venter på kontroll mot Lovdata).

### `bht_paakrevd` er tri-state

`true`/`false` = vurdert mot FOR-2011-12-06-1355 § 13-1. `NULL` = ikke
verifisert, og Harvey skal da flagge kravet for manuell vurdering framfor å anta
at BHT er unødvendig. «Vet ikke» er et ærligere svar enn «nei».

---

## 3. Pipelinen

```
Skjema → Brønnøysund → NACE-oppslag → <bransjekrav> som avgrenset data
   │
   ├─ 1. Harvey      Lovkartlegging          → validert JSON
   ├─ 2. Donna       Kapittelplan            → validert JSON + dekningsport
   ├─ 3. Mike        Kapittelinnhold         → 6 kapitler parallelt, port per kapittel
   ├─ 4. KODE        Sammenstilling          → forside, TOC, endringslogg, vedlegg
   │                 + kvalitetsport + faktaport
   ├─ 5. Louis       Kvalitetskontroll       → funnliste, maks 1 reparasjonsrunde
   ├─ 6. Jessica     Endelig verifisering    → dekning + konsistens på tvers
   └─ 7-8. KODE      Lagring og eksport      → 23 filer
```

Alt ligger i `pipeline.py:run()`. Feiler noe, settes sesjonen til `failed` og
unntaket bobler opp.

### Agentene

| Agent | Oppgave | Kontrakt |
|---|---|---|
| **Harvey** | Hvilke lover gjelder denne bedriften | JSON, validert, 2 forsøk |
| **Donna** | Hvilke kapitler må håndbøkene ha | JSON, validert + dekningsport |
| **Mike** | Skriver ett kapittel per API-kall | Markdown, port per kapittel |
| **Louis** | Finner feil i ett ferdig dokument | Funnliste med alvorsgrad |
| **Jessica** | Ser begge håndbøkene samlet | Dekning + konsistens |

`agents/*.md` beskriver personlighet og ansvar. `prompts/*_system.md` er det som
faktisk sendes til modellen.

### Hvorfor Mike skriver ett kapittel om gangen

Ett stort kall som skriver hele håndboken gir ingen kontrollpunkter underveis og
treffer taket for utdata. Ett kall per kapittel gir en kvalitetsport mellom hver,
og lar kapitlene skrives **parallelt** — de er uavhengige av hverandre.

`MIKE_PARALLELLE` (standard 6) styrer hvor mange som kjører samtidig. Målt effekt:
Mike gikk fra ~14 minutter til ~2,5 for 13 kapitler.

Determinismen er bevart fordi resultatene indekseres etter **planens** rekkefølge,
aldri etter hvem som blir ferdig først. To mock-kjøringer gir bit-identiske
dokumenter.

### Reparasjonsrunden

Louis leverer funn per kapittel. `_louis_runde` skriver om **bare** kapitlene med
funn, parallelt, og syr dokumentet sammen igjen i original rekkefølge. Målt:
~38 sekunder, mot ~15 minutter da alle kapitler ble skrevet om sekvensielt.

**Begrensning verdt å kjenne:** reparasjonsrunden kan omskrive kapitler som
finnes, men ikke opprette nye. Ber Louis om et kapittel som mangler i planen, er
leveransen tapt uansett hvor godt Mike skriver. Derfor ligger dekningsporten hos
Donna, der det fortsatt lar seg rette — se `_PLANKRAV`.

---

## 4. Kvalitetsportene

Portene er **kode, ikke modellvurderinger**. De kan ikke overtales og kan ikke ha
en dårlig dag.

### Per kapittel — `_kapittelfeil`
- Riktig overskrift
- Minst `MIN_KAPITTEL_TEGN` (400)
- Ingen gjenglemte plassholdere

Feiler den, får Mike funnene og prøver på nytt. To forsøk, så stopper leveransen.

### Per kapittelplan — `_plan_mangler`
Emner Harvey har kartlagt må ha et kapittel i Donnas plan. I dag: varsling etter
AML kap. 2A, og arbeidsreglement når `arbeidsreglement_paakrevd` er `true`.

Merk at flaggbaserte krav ser på **verdien**, ikke om feltnavnet finnes i JSON-en
— et tekstsøk ville slått til på alle bedrifter, også de som ikke er omfattet.

### Per sammensatt dokument — `_kvalitetsfeil`
- Alle planlagte kapitler er til stede
- Ingen plassholdere utenom de kanoniske
- **HMS-mål**: minst tre mål i tabell, der måltall og frist inneholder tall
  (IK-forskriften § 5 andre ledd nr. 4)
- **IK-dekning**: hvert av kravene nr. 4–8 har et *eget* kapittel, med treff i
  både overskrift og innhold — så generell standardtekst ikke kan «dekke» et krav
  Mike aldri skrev om

### Hjemmelskontroll — `lovregister.hjemmelsfeil`
Slår siterte paragrafer opp i `lovhjemler` og melder to ting, begge som
oppslag uten skjønn: en paragraf som er **opphevet**, og en paragraf som ikke
finnes i et kapittel vi har registrert **komplett**. For lover uten
kapittelprefiks (IK-forskriften § 5, ferieloven § 10) er hele loven enheten, og
slike lover legges bare inn komplette.

Registeret dekker hele AML, IK-forskriften, ferieloven, OTP-loven,
likestillings- og diskrimineringsloven og folketrygdloven kap. 8–9. Bare
paragrafer eksplisitt merket med lovnavn kontrolleres (`lovregister.LOVNAVN`) —
«§ 5-2» alene kan tilhøre hvilken som helst lov. Kapitler som ikke er
registrert, sies det ingenting om.

Porten finnes fordi kontrollen tidligere lå hos Louis, som resonnerer om
paragrafnumre fra hukommelsen uten kilde. Han ba en gang Mike endre
meldeplikten til Arbeidstilsynet fra § 5-2 til § 5-1 — fra riktig til galt — og
underkjente ham i neste runde for nettopp det. En kontroll som er like usikker
som det den kontrollerer, gjør skade når den tar feil.

### Faktakonsistens — `_faktafeil`
- Bedriftsnavnet skrevet med samme bokstavbruk overalt
- Ingen frist som ligger før dokumentdatoen

### Louis' alvorsgradering — `_blokkerende`
`KRITISK` (lovfeil) og `HØY` (manglende påkrevd innhold) stopper leveransen.
`MIDDELS` forsøkes rettet, men blokkerer ikke.

Skillet er nødvendig: Louis er instruert til å være pedantisk, og en port som
krevde tom funnliste gjorde ham matematisk ute av stand til å godkjenne noe.
Et dokument med en klønete formulering er fortsatt et gyldig HMS-system; ett med
feil paragrafhenvisning er det ikke.

### Hard feil
`stop_reason == "max_tokens"` avbryter kjøringen. Et avkuttet compliance-dokument
er verre enn ingen leveranse.

---

## 5. Grunnprinsippet: data, kode eller prompt

Hver gang noe skal legges til, er første spørsmål hvor det hører hjemme.

| Hører hjemme i | Hva | Hvorfor |
|---|---|---|
| **Supabase** | Alt som er sant i verden og kan endre seg — lovhjemler, forskrifter, bransjekrav | Kan verifiseres, dateres og oppdateres uten kodeendring |
| **Kode** | Regler som ikke skal kunne overtales — porter, faktaregister, datosjekk | Deterministisk, testbart |
| **Prompt** | Bare *hvordan* det skrives — tone, struktur, disposisjon | Aldri hva som er sant |

En lovregel skrevet inn i en prompt eldes stille. `AML § 14-8` ble endret
1. juli 2024; en prompt som sier noe annet, sier det fortsatt om to år uten at
noen merker det. Samme regel i `nace_forskriftskrav` har `verifisert_dato` og
kan revideres.

### Faktaregisteret

`_faktaregister` skiller to ting modellen ellers behandler likt:

- **Kjente fakta** — bedriftsnavn, org.nr, antall ansatte, dokumentdato.
  Gjengis nøyaktig, aldri omskrevet.
- **Ikke oppgitt** — lønnsdato, BHT-leverandør, pensjonsleverandør, arbeidstid,
  tariffavtale. Bruk plassholderen ordrett; ikke finn på en verdi.

Uten dette skillet finner modellen på en verdi, og en *annen* verdi neste gang
temaet nevnes. Første ekte leveranse hadde «lønn utbetales normalt den 1.» i
kapittel 2 og «den 25.» i kapittel 5 av samme dokument — fordi ingen spurte om
lønnsdato, og hvert kapittel ble skrevet uavhengig.

Registeret er en instruksjon, og instruksjoner glipper over 120 000 tegn.
Derfor håndhever `_faktafeil` det samme i kode.

---

## 6. Robusthet

### Nettverk
Adaptiv thinking gir lange stillheter i strømmen — modellen tenker uten å sende
tokens. Standardtimeouten tåler det ikke. Klienten kjører derfor med 900 sekunders
read-timeout, og `_kall_modell` har en egen retry-løkke rundt hele strømmen:
SDK-ens innebygde retry dekker bare feil som oppstår *før* strømmen åpnes.

`_er_nettverksfeil` skiller feil som går over av seg selv (timeout, brutt
forbindelse, rate limit, 5xx) fra feil som er endelige (ugyldig forespørsel, feil
nøkkel) — en gal nøkkel skal ikke bruke fire forsøk på å bekrefte seg selv.

Observerte og håndterte: `read operation timed out`, `[Errno 35] Resource
temporarily unavailable`, `[Errno 54] Connection reset by peer`.

### Avbrutte jobber
Pipelinen kjører som `BackgroundTask` i serverprosessen. Restarter serveren —
deploy, krasj, Ctrl-C — forsvinner jobben, men raden i basen blir stående på
`running` for alltid, og kunden venter på noe som aldri kommer.

`rydd_foreldreloese_kjoringer` kjører ved oppstart og merker alt som fortsatt står
som `running` etter 45 minutter som feilet.

### Prompt caching
Systemprompten og Harveys lovanalyse er identiske i alle Mikes kapittelkall.
`_bruker_innhold` legger den delte konteksten først med `cache_control`, og det
som varierer per kapittel til slutt — caching er et prefiksoppslag, så
rekkefølgen er ikke kosmetisk.

---

## 7. Leveransen

Alt havner i `output/<session_id>/`, prefikset med bedriftsnavn og dato.

| Dokument | Formater | Hjemmel |
|---|---|---|
| HMS-håndbok | md, json, docx, pdf | IK-forskriften § 5 andre ledd nr. 4–8 |
| Personalhåndbok | md, json, docx, pdf | AML kap. 2A og 14, ferieloven, OTP |
| Risikovurdering | xlsx, json, docx, pdf | IK-forskriften § 5 andre ledd nr. 6 |
| Årlig gjennomgang | docx, pdf | IK-forskriften § 5 andre ledd nr. 8 |
| Innføringsplan | docx, pdf | IK-forskriften § 4 |
| 7 skjemaer | docx | AML § 3-1, § 4-6, § 14-5, ftrl. § 8-24, GDPR |

Sammenstillingen er deterministisk: forside, innholdsfortegnelse, endringslogg og
vedleggsoversikt lages av kode, ikke av modellen.

**Innføringsdelen** er verdt å merke seg. IK-forskriften § 4 krever at
internkontroll *innføres og utøves*, ikke bare skrives. Håndboken åpner derfor med
«Slik tar dere håndboken i bruk» — terskelstyrte steg og et årshjul. En perm ingen
har vedtatt er ikke et system, og det er der de fleste bedrifter faller igjennom.

---

## 8. Sikkerhet

- Alle `/api/`-endepunkter krever `X-API-Key`. Nøkkelen oppgis av brukeren og er
  aldri innbakt i HTML
- Backend bruker Supabase `service_role`; anon har kun lesetilgang til NACE-tabellen
- CSP uten inline-script; all markdown saneres med DOMPurify før rendering
- Brukerfelter sendes som avgrenset data i `<bedriftsinformasjon>` — aldri som
  instruksjoner. Regex-filteret mot prompt injection er et sekundært lag
- Rate limiting på alle endepunkter
- Sti-oppslag ved nedlasting verifiserer at filen ligger innenfor sesjonsmappen

---

## 9. Kjøring lokalt

```bash
pip install -r requirements.txt
MOCK_MODE=false python3 -m uvicorn server:app --port 8010 --reload
```

Nødvendige nøkler i `.env`: `ANTHROPIC_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`,
`API_KEY`. Er API-nøkkelen identitetskoblet, trengs også
`ANTHROPIC_WORKSPACE_ID`.

`MOCK_MODE=true` kjører hele pipelinen uten API-kostnader. Mock-dataene er laget
for å passere de samme portene som produksjon — mock som ikke tåler portene,
tester noe annet enn det systemet faktisk gjør.

`python3 tests/ekte_kjoring.py` kjører én ekte generering ende til ende og skriver
status per agent underveis.

### Målt ytelse

| Steg | Tid |
|---|---|
| Harvey | ~30 sek |
| Donna | ~2,5 min |
| Mike (13 kapitler, parallelt) | ~2,5 min |
| Louis per dokument | ~4 min |
| Reparasjonsrunde | ~40 sek |
| Jessica | ~1 min |
| **Totalt med to reparasjonsrunder** | **~23 min** |

Kostnad: 15–20 kr per generering med Sonnet 5.

---

## 10. Kjente begrensninger

Disse er reelle og bevisste å kjenne til:

1. **Filene overlever ikke en utrulling.** De skrives til containerdisken.
   Markdown ligger trygt i `handbooks`, men PDF, Word og Excel forsvinner ved
   neste deploy. Skal til Supabase Storage.
2. **Én delt API-nøkkel.** Alle kunder får samme nøkkel; den kan ikke trekkes
   tilbake for én uten å bytte for alle.
3. **Reparasjonsrunden kan ikke opprette kapitler** — se punkt 3 over.
4. **Seks uverifiserte hjemler for elektro** venter på kontroll mot Lovdata.
5. **«Tenker» og «død» ser identiske ut** i basen. `agent_runs` oppdateres bare
   når det kommer tekst, og under thinking er strømmen stille.
6. **Ingen juristgjennomgang ennå.** Lovpåstandene er kontrollert mot
   Lovdata, men ikke vurdert av en jurist — se `JURISTGJENNOMGANG.md`.

En komplett, prioritert liste over forbedringer ligger i funnlisten fra
31.08.2026.

---

## 11. Filkart

```
hms-generator/
├── ARKITEKTUR.md      # denne filen
├── CLAUDE.md          # arbeidsregler
├── README.md          # kom i gang
├── AGENTREVIEW.md     # agentreview med målbilde
├── server.py          # FastAPI: auth, rate limiting, oppstartsopprydding
├── pipeline.py        # agentene, portene, parallellisering, Excel/Word-skjemaer
├── eksport.py         # JSON/DOCX/PDF, HMS-målkontroll, IK-dekning, innføringsplan
├── nace_krav.py       # NACE-oppslag → <bransjekrav> til Harvey
├── lovregister.py     # paragrafoppslag → <lovregister> til Mike + hjemmelsport
├── brreg.py           # Enhetsregisteret, MOD11-validering, norske feilmeldinger
├── agents/            # hvem agentene er
├── prompts/           # hva som sendes til modellen
├── migrations/        # 001 skjema · 002 seed · 003 elektro · 004–005 lovhjemler
├── tests/             # pytest: porter, lovregister, kravmotor + ende-til-ende
├── ui/                # landing.html (salg) · index.html + app.js (generator)
└── output/            # genererte filer (ignorert av git)
```
