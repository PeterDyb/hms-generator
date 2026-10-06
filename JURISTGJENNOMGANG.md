# Juristgjennomgang — grunnlag

**Status:** Forhåndskontroll mot Lovdata er gjort 06.10.2026. **Selve
juristgjennomgangen gjenstår.** Dette dokumentet er ikke en juridisk vurdering.
Det sier hvilke påstander systemet gjør om gjeldende rett, hvilke som er
kontrollert mot lovteksten, og hvilke spørsmål en jurist må ta stilling til.

Uten en jurists gjennomgang bør håndbøkene ikke selges som juridisk
kvalitetssikret.

## Hva som er kontrollert, og hvordan

Hver påstand under er sammenlignet med lovteksten slik den sto på Lovdata
06.10.2026. «Stemmer» betyr at påstanden står i lovteksten. Det betyr ikke at
den er en fullstendig framstilling av rettstilstanden.

### Paragrafnumre — kode, ikke skjønn

`lovhjemler` inneholder 362 paragrafer, alle med `kilde_url` og
`verifisert_dato`:

| Lov | Omfang |
|---|---|
| Arbeidsmiljøloven | hele loven, kap. 1–20, 2A og 14A (197) |
| Internkontrollforskriften | hele (11) |
| Ferieloven | hele (18) |
| OTP-loven | hele (11) |
| Likestillings- og diskrimineringsloven | hele (49) |
| Folketrygdloven | kap. 8 og 9 (76) |

Hjemmelsporten (`lovregister.py`) stopper paragrafer som ikke finnes, og
paragrafer som er opphevet, når de er merket med lovnavn. Den vurderer ikke om
en paragraf er brukt om riktig tema. Det må en jurist gjøre.

### Tall og terskler som stemmer med lovteksten

| Påstand | Hjemmel |
|---|---|
| Verneombud i alle virksomheter; annen ordning kan avtales skriftlig under 5 ansatte | AML § 6-1 (1) |
| AMU fra 30 ansatte; 10–30 hvis en part krever det | AML § 7-1 (1) |
| Oppfølgingsplan senest etter 4 uker; dialogmøte 1 senest innen 7 uker | AML § 4-6 (3), (4) |
| Dialogmøte 2 senest når arbeidsuførheten har vart i 26 uker (NAV) | ftrl. § 8-7 a |
| Alminnelig arbeidstid 9 t/24 t og 40 t/7 dager | AML § 10-4 (1) |
| Overtid 10 t/7 dager, 25 t/4 uker, 200 t/52 uker | AML § 10-6 (4) |
| Hvile 11 t/24 t og 35 t/7 dager | AML § 10-8 (1), (2) |
| Pause over 5,5 t; minst 30 min ved minst 8 t | AML § 10-9 (1) |
| Prøvetid inntil 6 måneder; 14 dagers frist | AML § 15-6 (3), § 15-3 (7) |
| Oppsigelsesfrister 1/2/3 mnd; 4/5/6 mnd ved 50/55/60 år | AML § 15-3 |
| Arbeidsreglement: industri, handel og kontor med mer enn 10 ansatte | AML § 14-16 (1) |
| Ferie 25 virkedager; ekstraferie 6 dager fra 60 år | ferieloven § 5 |
| Feriepenger 10,2 %; +2,3 prosentpoeng over 60 år | ferieloven § 10 (2), (3) |
| Arbeidsgiverperiode 16 kalenderdager | ftrl. § 8-19 |
| Omsorgspenger 10 dager; 15 ved mer enn to barn; 20/30 ved aleneomsorg | ftrl. § 9-6 |
| OTP minst 2 % av lønn opp til 12G | OTP-loven § 4 |

### Feil som er rettet i denne runden

1. **Lønnskartlegging** var hjemlet i likestillings- og diskrimineringsloven
   § 26 a med plikt fra «50 eller flere» ansatte. Plikten står i § 26 andre
   ledd og gjelder private virksomheter med **mer enn** 50 ansatte (20–50 når
   en part krever det). § 26 a er redegjørelsesplikten. Rettet i Harvey,
   Donna og mock-terskelen (`> 50`).
2. **Arbeidsavtalemalen** viste til AML § 14-6 med bokstaver fra før
   lovendringen i 2024 (prøvetid som «d», ferie som «k», pensjon som «l» osv.).
   Alle bokstavene er rettet etter dagens tekst. Malen har også fått felt for
   midlertidig ansettelse med grunnlag (bokstav e), arbeid utover avtalt
   arbeidstid (bokstav m) og skriftlig oppsigelse.
3. **IK-forskriften § 5** ble beskrevet med bokstavene (a)–(e) i Louis-prompten.
   Punktene er nummerert, og dokumentasjonskravet gjelder nr. 4–8.
4. **AML § 3-4** (tiltak for fysisk aktivitet) sto som hjemmel for
   sykefraværsoppfølging hos Harvey. Fjernet; hjemmelen er § 4-6.
5. **Egenmelding** ble omtalt som «maks 4 ganger per 12 måneder, lovens
   minimum». Etter ftrl. § 8-24 kan egenmelding brukes inntil 3 kalenderdager
   om gangen etter to måneders ansettelse. Fire fravær på 12 måneder er
   vilkåret for at arbeidsgiver *kan* frata retten (§ 8-27), ikke en
   lovfestet grense.
6. **Feriepenger over 60 år**: at tillegget bare beregnes av grunnlag opp til
   6G manglet.
7. **Skriftlig arbeidsavtale «innen 7 dager»** gjelder bare arbeidsforhold over
   en måned. Kortere arbeidsforhold og utleie krever avtale umiddelbart (AML
   § 14-5 (2), (3)).
8. **Lovdata-lenken** for AML kapittel 15 pekte på kapittel 14 A.

## Spørsmål en jurist må ta stilling til

Disse kan ikke avgjøres ved å slå opp i lovteksten. Det er forståelse,
praksis eller avgrensning.

1. **Hovedferie.** Promptene sa «3 uker sammenhengende». Ferieloven § 7 (1)
   sier at hovedferie «som omfatter 18 virkedager» kan kreves i
   hovedferieperioden. Formuleringen er endret til å følge lovteksten. Er det
   riktig å ikke love «sammenhengende»?
2. **OTP-plikt.** Håndboken omtaler OTP som obligatorisk. OTP-loven § 1 har
   egne vilkår for hvilke foretak som omfattes (bl.a. stillingsandeler og
   årsverk). Bør Harvey sette et `otp_paakrevd`-flagg ut fra antall ansatte og
   stillingsandeler, slik det gjøres for verneombud og AMU?
3. **OTP fra 13 år, ingen stillingsgrense.** Påstanden hører hjemme i
   innskuddspensjonsloven og tjenestepensjonsloven, som ikke er i registeret.
   Ikke kontrollert.
4. **Utvidet egenmelding.** Skjemaet tilbyr «utvidet ordning etter bedriftens
   egen ordning». Er det tilstrekkelig at håndboken viser til at
   arbeidsgiver kan gi slik rett (§ 8-24), og at tillitsvalgte skal tas med i
   drøftingen?
5. **Bransjekrav i `nace_forskriftskrav`.** Forskriftshjemlene per NACE-kode
   ble kontrollert da de ble lagt inn (se migrering 002/003). Bransjene er
   ikke vurdert av en jurist.
6. **Tema-riktighet.** Porten fanger paragrafer som ikke finnes. Den fanger
   ikke en gyldig paragraf brukt om feil tema (slik § 12-8 ammefri en gang ble
   brukt om all tilrettelegging). En jurist bør lese minst én komplett HMS- og
   personalhåndbok for hver risikoklasse.
7. **Lover utenfor registeret.** Personopplysningsloven/GDPR,
   yrkesskadeforsikringsloven, forskrift om organisering, ledelse og
   medvirkning og forskrift om utførelse av arbeid siteres, men kontrolleres
   ikke av porten.

## Forslag til gjennomgang

1. Les de faste påstandene i `prompts/harvey_system.md`,
   `prompts/donna_system.md` og `prompts/mike_system.md` (avsnittene med tall
   og frister).
2. Les én generert HMS-håndbok og én personalhåndbok fra `output/` for en
   bedrift i hver risikoklasse (lav, middels, høy).
3. Les skjemamalene: arbeidsavtale, egenmeldingsskjema og oppfølgingsplan
   (`pipeline.py`, `generate_word_forms`).
4. Svar på spørsmålene over. Svar som endrer hva som er sant, legges i
   Supabase eller kode, ikke bare i promptene (se `ARKITEKTUR.md`).
