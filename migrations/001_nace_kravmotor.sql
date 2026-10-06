-- NACE-basert kravmotor: skjema
--
-- Bakgrunn: harvey_nace_krav hadde kolonnen «forskrifter text[]» — en flat liste
-- med strenger. Den kan ikke bære en hjemmel strukturert (forskrift + nummer +
-- paragraf + hva kravet er), og et compliance-produkt må kunne vise NØYAKTIG
-- hvilken paragraf et krav kommer fra. Derfor får hver forskriftshenvisning nå
-- en egen rad, med kilde-URL og dato for når henvisningen sist ble verifisert.
--
-- Kolonnen forskrifter[] beholdes urørt for bakoverkompatibilitet, men skal ikke
-- brukes av ny kode.

-- ─── Bransjetabellen utvides ────────────────────────────────────────────────

-- bht_paakrevd var NOT NULL DEFAULT false. Det tvinger fram et svar der vi ikke
-- har et: bransjelista ligger i forskrift om organisering, ledelse og medvirkning
-- § 13-1, og den er ikke verifisert for alle kodene under. NULL = «vet ikke,
-- må vurderes manuelt» er riktigere enn false = «nei, ikke påkrevd».
alter table public.harvey_nace_krav
  alter column bht_paakrevd drop default,
  alter column bht_paakrevd drop not null;

comment on column public.harvey_nace_krav.bht_paakrevd is
  'Tri-state. true/false = vurdert mot forskrift om organisering, ledelse og '
  'medvirkning (FOR-2011-12-06-1355) § 13-1. NULL = ikke verifisert — Harvey '
  'skal da flagge kravet for manuell vurdering, ikke anta at BHT er unødvendig.';

-- HMS-dokumenttyper bransjen må ha utover standardsettet fra IK-forskriften § 5.
alter table public.harvey_nace_krav
  add column if not exists dokumentkrav text[] not null default '{}';

comment on column public.harvey_nace_krav.dokumentkrav is
  'Bransjespesifikke HMS-dokumenter som kommer I TILLEGG til dokumentasjonskravene '
  'i IK-forskriften § 5 andre ledd nr. 4-8.';

comment on column public.harvey_nace_krav.forskrifter is
  'UTGÅTT — bruk tabellen nace_forskriftskrav. Beholdt for bakoverkompatibilitet.';

-- ─── Én rad per konkret hjemmel ─────────────────────────────────────────────

create table if not exists public.nace_forskriftskrav (
  id                uuid primary key default gen_random_uuid(),
  nace_kode         text not null
                      references public.harvey_nace_krav(nace_kode) on delete cascade,
  forskrift_navn    text not null,
  -- Lovdata-identifikator, f.eks. FOR-2009-08-03-1028. Gjør henvisningen sporbar.
  forskrift_nummer  text not null,
  paragraf          text not null,          -- «§ 8», «kapittel 3A»
  krav              text not null,          -- hva bedriften faktisk må gjøre
  dokumenttype      text,                   -- hvilket HMS-dokument kravet utløser
  kilde_url         text,
  -- Når henvisningen sist ble kontrollert mot kilden. Regelverk endres; en
  -- hjemmel uten dato er en hjemmel ingen har sjekket.
  verifisert_dato   date,
  created_at        timestamptz not null default now(),

  constraint nace_forskriftskrav_unik unique (nace_kode, forskrift_nummer, paragraf)
);

create index if not exists nace_forskriftskrav_kode_idx
  on public.nace_forskriftskrav (nace_kode);

comment on table public.nace_forskriftskrav is
  'Bransjespesifikke hjemler per NACE-kode. Én rad = én paragraf. Kilde-URL og '
  'verifisert_dato gjør det mulig å svare på «hvor kommer denne henvisningen fra».';

-- ─── Tilgang ────────────────────────────────────────────────────────────────
-- Samme mønster som harvey_nace_krav: backend bruker service_role, anon får
-- kun lese. Ingen skrivepolicy for anon.

alter table public.nace_forskriftskrav enable row level security;

drop policy if exists nace_forskriftskrav_les on public.nace_forskriftskrav;
create policy nace_forskriftskrav_les
  on public.nace_forskriftskrav
  for select
  to anon, authenticated
  using (true);
