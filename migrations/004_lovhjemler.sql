-- Hjemmelsregister for arbeidsmiljøloven
--
-- BAKGRUNN
-- Tre leveranser på rad stoppet på paragrafhenvisninger, og hver gang var
-- rotårsaken den samme: en modell som husket et paragrafnummer i stedet for å
-- slå det opp.
--
--   * Donna-prompten beskrev § 2A-7 som «krav til varslingsrutinens innhold».
--     Paragrafen regulerer taushetsplikt ved ekstern varsling.
--   * § 12-8 (ammefri) sto som eneste hjemmel for et kapittel om
--     risikovurdering og tilrettelegging, så Mike strakk den over alt.
--   * Louis ba Mike endre meldeplikten til Arbeidstilsynet fra § 5-2 til § 5-1
--     — fra riktig til galt — og underkjente ham i neste runde for nettopp det.
--     I samme kjøring erklærte han § 2A-7 for ikke-eksisterende etter selv å ha
--     oppgitt den som riktig hjemmel runden før.
--
-- Louis har ingen oppslagskilde. Kontrollen var derfor ikke mer pålitelig enn
-- det den kontrollerte, og kunne gjøre dokumentet dårligere.
--
-- Denne tabellen er kilden. Alle radene er kontrollert mot Lovdata 15.09.2026.
-- Samme mønster som nace_forskriftskrav: en hjemmel uten verifisert_dato er en
-- hjemmel ingen har kontrollert.

create table if not exists public.lovhjemler (
  id               uuid primary key default gen_random_uuid(),
  lov_kortnavn     text not null,
  lov_navn         text not null,
  lov_nummer       text not null,
  kapittel         text not null,
  paragraf         text not null,
  overskrift       text not null,
  opphevet         boolean not null default false,
  kilde_url        text,
  verifisert_dato  date,
  created_at       timestamptz not null default now(),
  unique (lov_kortnavn, paragraf)
);

comment on table public.lovhjemler is
  'Paragrafregister per lov. Ett kapittel legges alltid inn KOMPLETT, slik at '
  'fravær av en paragraf i et registrert kapittel betyr at paragrafen ikke '
  'finnes — det er dette som gjør hjemmelskontrollen til et oppslag i stedet '
  'for en modellvurdering.';

comment on column public.lovhjemler.opphevet is
  'true = paragrafen er opphevet og skal aldri siteres som gjeldende rett.';

comment on column public.lovhjemler.verifisert_dato is
  'Dato paragrafen sist ble kontrollert mot kilde_url. NULL = ikke kontrollert.';

alter table public.lovhjemler enable row level security;

create index if not exists lovhjemler_kapittel_idx
  on public.lovhjemler (lov_kortnavn, kapittel);

-- ─── Arbeidsmiljøloven — ni komplette kapitler ──────────────────────────────

insert into public.lovhjemler
  (lov_kortnavn, lov_navn, lov_nummer, kapittel, paragraf, overskrift, opphevet, kilde_url, verifisert_dato)
values
  -- Kapittel 2 — arbeidsgivers og arbeidstakers plikter
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2','§ 2-1','Arbeidsgivers plikter',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_2','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2','§ 2-2','Arbeidsgivers plikter overfor andre enn egne arbeidstakere',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_2','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2','§ 2-3','Arbeidstakers medvirkningsplikt',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_2','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2','§ 2-4','Opphevet',true,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_2','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2','§ 2-5','Opphevet',true,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_2','2026-09-15'),

  -- Kapittel 2A — varsling
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2A','§ 2A-1','Rett til å varsle om kritikkverdige forhold i virksomheten',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_3','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2A','§ 2A-2','Fremgangsmåte ved varsling',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_3','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2A','§ 2A-3','Arbeidsgivers aktivitetsplikt ved varsling',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_3','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2A','§ 2A-4','Forbud mot gjengjeldelse',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_3','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2A','§ 2A-5','Oppreisning og erstatning ved brudd på forbudet mot gjengjeldelse',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_3','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2A','§ 2A-6','Plikt til å utarbeide rutiner for intern varsling',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_3','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2A','§ 2A-7','Taushetsplikt ved ekstern varsling til offentlig myndighet',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_3','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','2A','§ 2A-8','Diskrimineringsnemnda',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_3','2026-09-15'),

  -- Kapittel 3 — virkemidler i arbeidsmiljøarbeidet
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','3','§ 3-1','Krav til systematisk helse-, miljø- og sikkerhetsarbeid',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_4','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','3','§ 3-2','Særskilte forholdsregler for å ivareta sikkerheten',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_4','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','3','§ 3-3','Bedriftshelsetjeneste',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_4','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','3','§ 3-4','Vurdering av tiltak for fysisk aktivitet',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_4','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','3','§ 3-5','Plikt for arbeidsgiver til å gjennomgå opplæring i helse-, miljø- og sikkerhetsarbeid',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_4','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','3','§ 3-6','Opphevet',true,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_4','2026-09-15'),

  -- Kapittel 4 — krav til arbeidsmiljøet
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','4','§ 4-1','Generelle krav til arbeidsmiljøet',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_5','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','4','§ 4-2','Krav til tilrettelegging, medvirkning og utvikling',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_5','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','4','§ 4-3','Krav til det psykososiale arbeidsmiljøet',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_5','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','4','§ 4-4','Krav til det fysiske arbeidsmiljøet',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_5','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','4','§ 4-5','Særlig om kjemisk og biologisk helsefare',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_5','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','4','§ 4-6','Særlig om tilrettelegging for arbeidstakere med redusert arbeidsevne',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_5','2026-09-15'),

  -- Kapittel 5 — registrering og melding
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','5','§ 5-1','Registrering av skader og sykdommer',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_6','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','5','§ 5-2','Arbeidsgivers varslings- og meldeplikt',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_6','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','5','§ 5-3','Leges meldeplikt',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_6','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','5','§ 5-4','Produsenter og importører av kjemikalier og biologisk materiale',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_6','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','5','§ 5-5','Produsenter, leverandører og importører av maskiner og annet arbeidsutstyr',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_6','2026-09-15'),

  -- Kapittel 6 — verneombud
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','6','§ 6-1','Plikt til å velge verneombud',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_7','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','6','§ 6-2','Verneombudets oppgaver',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_7','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','6','§ 6-3','Verneombudets rett til å stanse farlig arbeid',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_7','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','6','§ 6-4','Særskilte lokale eller regionale verneombud',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_7','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','6','§ 6-5','Utgifter, opplæring mv.',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_7','2026-09-15'),

  -- Kapittel 7 — arbeidsmiljøutvalg
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','7','§ 7-1','Plikt til å opprette arbeidsmiljøutvalg',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_8','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','7','§ 7-2','Arbeidsmiljøutvalgets oppgaver',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_8','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','7','§ 7-3','Særskilte lokale arbeidsmiljøutvalg',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_8','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','7','§ 7-4','Utgifter, opplæring mv.',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_8','2026-09-15'),

  -- Kapittel 10 — arbeidstid
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-1','Definisjoner',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-2','Arbeidstidsordninger',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-3','Arbeidsplan',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-4','Alminnelig arbeidstid',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-5','Gjennomsnittsberegning av den alminnelige arbeidstid',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-6','Overtid',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-7','Oversikt over arbeidstiden',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-8','Daglig og ukentlig arbeidsfri',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-9','Pauser',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-10','Søndagsarbeid',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-11','Nattarbeid',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-12','Unntak',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','10','§ 10-13','Tvisteløsning',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_11','2026-09-15'),

  -- Kapittel 12 — rett til permisjon
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-1','Svangerskapskontroll',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-2','Svangerskapspermisjon',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-3','Omsorgspermisjon',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-4','Fødselspermisjon',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-5','Foreldrepermisjon',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-6','Delvis permisjon',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-7','Varslingsplikt',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-8','Ammefri',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-9','Barns og barnepassers sykdom',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-10','Omsorg for og pleie av nærstående',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-11','Utdanningspermisjon',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-12','Militærtjeneste mv.',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-13','Offentlige verv',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-14','Tvisteløsning',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-15','Religiøse høytider',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','12','§ 12-16','Forskrifter ved utbrudd eller fare for utbrudd av allmennfarlig smittsom sykdom',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_13','2026-09-15'),

  -- Kapittel 15 — opphør av arbeidsforhold
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-1','Drøfting før beslutning om oppsigelse',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-2','Informasjon og drøfting ved masseoppsigelser',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-3','Oppsigelsesfrister',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-4','Formkrav ved oppsigelse',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-5','Virkninger av formfeil ved oppsigelse',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-6','Oppsigelsesvern i arbeidsavtaler med bestemt prøvetid',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-7','Vern mot usaklig oppsigelse',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-8','Oppsigelsesvern ved sykdom',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-9','Oppsigelsesvern ved svangerskap, og etter fødsel eller adopsjon',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-10','Oppsigelsesvern ved militærtjeneste mv.',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-11','Retten til å fortsette i stillingen',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-12','Virkninger av usaklig oppsigelse mv.',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-13','Suspensjon',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-13a','Opphør av arbeidsforhold grunnet alder',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-14','Avskjed',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-15','Attest',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-16','Virksomhetens øverste leder',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15'),
  ('AML','Arbeidsmiljøloven','LOV-2005-06-17-62','15','§ 15-17','Oppsigelse ved arbeidskonflikt',false,'https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_16','2026-09-15')
on conflict (lov_kortnavn, paragraf) do nothing;

-- Kapittel 14 er IKKE lagt inn komplett: oppslaget ga bare de sentrale
-- paragrafene, ikke hele lista. Et delvis kapittel ville gjort porten til en
-- falsk-positiv-maskin — den ville meldt gyldige paragrafer som ukjente.
-- Legg inn kapittelet når hele lista er kontrollert.
