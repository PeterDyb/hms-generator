-- NACE-konsolidering + full bransjedekning for elektro
--
-- BAKGRUNN
-- Tabellen bar to kodeformater side om side: gjeldende femsifrede SN2007-koder
-- («43.210») og eldre koder med næringsbokstav («F43.21»). Kartleggingen viste
-- et entydig mønster:
--
--   17 femsifrede koder  → 3–4 forskriftshjemler og utfylte dokumentkrav
--   28 bokstavkoder      → NULL hjemler, NULL dokumentkrav — tomme skall
--
-- De to formatene motsier hverandre der de overlapper: 43.210 har risikonivå
-- «høyt» og to dokumentkrav, F43.21 har «svært høyt» og ingen. Velger kunden
-- den gamle koden fra nedtrekkslisten, får hen en håndbok uten bransjetilpasning
-- i det hele tatt — og Jessica godkjenner den, fordi hun kontrollerer mot en
-- tom kravliste.
--
-- Bokstavkodene er dessuten ikke søkbare fra et Brønnøysund-oppslag (Brreg
-- oppgir SN2007), så de kan aldri nås gjennom org.nr-veien. De skjules i stedet
-- for å slettes: eksisterende sesjoner peker på dem via fremmednøkkel.
--
-- Femten bransjer med reell dekning er et bedre produkt enn 45 der 28 er tomme.

-- ─── 1. Skill gjeldende koder fra utgåtte ───────────────────────────────────

alter table public.harvey_nace_krav
  add column if not exists gjeldende boolean not null default true;

comment on column public.harvey_nace_krav.gjeldende is
  'Vises i bransjevelgeren. false = eldre kode med næringsbokstav (F41, Q86). '
  'De er ikke søkbare fra Brønnøysund og har ingen forskriftshjemler, men '
  'beholdes fordi tidligere sesjoner refererer til dem.';

-- En kode uten en eneste forskriftshjemmel gir ingen bransjetilpasning.
-- Det er det som skiller de to formatene, så det er det vi måler på —
-- ikke kodeformatet i seg selv.
update public.harvey_nace_krav h
   set gjeldende = false
 where not exists (
   select 1 from public.nace_forskriftskrav f where f.nace_kode = h.nace_kode
 );

-- ─── 2. Elektro: fra tre hjemler til full bransjedekning ────────────────────
--
-- Kritikken av den første ekte leveransen fant at et elektroforetak ble
-- behandlet som et generisk byggfirma. Årsaken lå her: tabellen kjente SHA-plan,
-- fallsikring og sikkerhetsopplæring — ikke FEK, FSE, stoffkartotek eller
-- HMS-kort. Modellen dikter der dataene tier: den gjettet «hvert 3. år» på
-- FSE-førstehjelp (kravet er årlig) og fant opp en 2-metersgrense for
-- fallsikring som ikke finnes i regelverket.
--
-- MERK — verifisert_dato er bevisst NULL på alle radene under.
-- Forskriftsnumrene og kravene er riktige, men paragrafnumrene er IKKE slått
-- opp mot Lovdata. Å legge inn ukontrollerte paragrafhenvisninger som «bruk
-- nøyaktig disse» ville gjenta akkurat den feilen vi retter. Koden skiller nå
-- på verifisert_dato: uverifiserte rader sier til Harvey at temaet SKAL dekkes,
-- men at paragrafnummer ikke skal siteres. Sett datoen når hver rad er
-- kontrollert mot kilde_url.

insert into public.nace_forskriftskrav
  (nace_kode, forskrift_navn, forskrift_nummer, paragraf, krav, dokumenttype, kilde_url, verifisert_dato)
values
  ('43.210',
   'Forskrift om elektroforetak og kvalifikasjonskrav for arbeid knyttet til elektriske anlegg og elektrisk utstyr (FEK)',
   'FOR-2013-06-19-739',
   'hele forskriften',
   'Elektroforetak skal være registrert i Elvirksomhetsregisteret og ha faglig ansvarlig for arbeidet. Foretaket har egen internkontrollplikt for det elektrofaglige arbeidet, med DSB som tilsynsmyndighet — dette kommer i tillegg til internkontrollen etter IK-forskriften.',
   'Registrering i Elvirksomhetsregisteret; utpekt faglig ansvarlig',
   'https://lovdata.no/dokument/SF/forskrift/2013-06-19-739',
   null),

  ('43.210',
   'Forskrift om sikkerhet ved arbeid i og drift av elektriske anlegg (FSE)',
   'FOR-2006-04-28-458',
   'hele forskriften',
   'Alle som utfører arbeid på eller nær elektriske anlegg skal ha ÅRLIG opplæring og øvelse i førstehjelp ved el-ulykker. Det skal utpekes ansvarlig for arbeidet, og arbeidet skal risikovurderes med tanke på strømgjennomgang og lysbue.',
   'Dokumentert årlig FSE-opplæring med førstehjelp ved el-ulykker',
   'https://lovdata.no/dokument/SF/forskrift/2006-04-28-458',
   null),

  ('43.210',
   'Forskrift om HMS-kort på bygge- og anleggsplasser',
   'FOR-2016-12-01-1445',
   'hele forskriften',
   'Alle som utfører arbeid på bygge- eller anleggsplass skal ha gyldig HMS-kort utstedt av Arbeidstilsynet, og bære det synlig.',
   'HMS-kort for alle som arbeider på bygge- og anleggsplass',
   'https://lovdata.no/dokument/SF/forskrift/2016-12-01-1445',
   null),

  ('43.210',
   'Forskrift om utførelse av arbeid',
   'FOR-2011-12-06-1357',
   'stoffkartotek',
   'Virksomheten skal ha stoffkartotek over farlige kjemikalier som brukes. For elektro gjelder dette blant annet PU-skum, lim, rensevæsker og kontaktspray.',
   'Stoffkartotek med sikkerhetsdatablad',
   'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357',
   null),

  ('43.210',
   'Forskrift om utførelse av arbeid',
   'FOR-2011-12-06-1357',
   'asbest',
   'Arbeid som kan medføre eksponering for asbest krever kartlegging før arbeidet starter, tillatelse fra Arbeidstilsynet og særskilte vernetiltak. Relevant ved boring og gjennomføringer i bygg fra før 1985.',
   'Kartlegging av asbest før arbeid i eldre bygg',
   'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357',
   null),

  ('43.210',
   'Forskrift om utførelse av arbeid',
   'FOR-2011-12-06-1357',
   'støy og mekaniske vibrasjoner',
   'Eksponering for støy og hånd-arm-vibrasjon skal kartlegges og risikovurderes, med tiltak og hørselsvern. Relevant ved bruk av borhammer, meiselhammer og vinkelsliper.',
   'Kartlegging av støy- og vibrasjonseksponering',
   'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357',
   null);

-- Dokumentkravene bransjen må ha utover IK-forskriften § 5.
update public.harvey_nace_krav
   set dokumentkrav = array[
     'SHA-plan',
     'Dokumentert sikkerhetsopplæring for arbeidsutstyr',
     'Dokumentert årlig FSE-opplæring med førstehjelp ved el-ulykker',
     'Registrering i Elvirksomhetsregisteret med utpekt faglig ansvarlig',
     'HMS-kort for alle som arbeider på bygge- og anleggsplass',
     'Stoffkartotek med sikkerhetsdatablad'
   ]
 where nace_kode = '43.210';

-- ─── 3. Indeks ──────────────────────────────────────────────────────────────

create index if not exists harvey_nace_krav_gjeldende_idx
  on public.harvey_nace_krav (gjeldende)
  where gjeldende;
