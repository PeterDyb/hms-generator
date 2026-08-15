-- NACE-basert kravmotor: seed for de vanligste NACE-kodene blant norske SMB-er.
--
-- Alle forskriftsnumre og paragrafer under er slått opp mot Lovdata 15.08.2026,
-- ikke skrevet fra hukommelsen. verifisert_dato på hver rad sier når.
--
-- To feil i det gamle prompt-materialet ble funnet under verifiseringen:
--   * BHT-bransjekravet ble sitert som «FOR-2009-01-01-70». Det nummeret finnes
--     ikke. Kravet ligger i FOR-2011-12-06-1355 § 13-1.
--   * Kjøre- og hviletid ble sitert som «FOR-2007-02-02-190». Riktig er
--     FOR-2007-07-02-877.
--
-- bht_paakrevd er tri-state: true/false der bransjen er vurdert mot § 13-1,
-- NULL der den ikke er det. Bransjelista i § 13-1 lot seg ikke hente maskinelt,
-- så kun bygg/anlegg, helse og renhold er satt til true.

insert into public.harvey_nace_krav
  (nace_kode, nace_navn, nace_hovedgruppe, risikonivaa, bht_paakrevd, dokumentkrav)
values
  ('62.010', 'Programmeringstjenester', 'Informasjon og kommunikasjon', 'lavt', false,
   '{}'),
  ('70.220', 'Bedriftsrådgivning og annen administrativ rådgivning', 'Faglig og teknisk tjenesteyting', 'lavt', false,
   '{}'),
  ('47.111', 'Butikkhandel med bredt vareutvalg, hovedvekt nærings- og nytelsesmidler', 'Varehandel', 'middels', null,
   '{"Rutine ved vold og trusler","Rutine for alenearbeid"}'),
  ('47.190', 'Annen butikkhandel med bredt vareutvalg', 'Varehandel', 'middels', null,
   '{"Rutine ved vold og trusler","Rutine for alenearbeid"}'),
  ('56.101', 'Drift av restauranter og kafeer', 'Overnattings- og serveringsvirksomhet', 'middels', null,
   '{"HACCP-basert internkontroll for mattrygghet","Rutine ved vold og trusler"}'),
  ('56.102', 'Drift av gatekjøkken', 'Overnattings- og serveringsvirksomhet', 'middels', null,
   '{"HACCP-basert internkontroll for mattrygghet","Rutine ved vold og trusler"}'),
  ('41.200', 'Oppføring av bygninger', 'Bygge- og anleggsvirksomhet', 'høyt', true,
   '{"SHA-plan","Forhåndsmelding til Arbeidstilsynet","Oversiktsliste over alle på bygge- eller anleggsplassen"}'),
  ('43.210', 'Elektrisk installasjonsarbeid', 'Bygge- og anleggsvirksomhet', 'høyt', true,
   '{"SHA-plan","Dokumentert sikkerhetsopplæring for arbeidsutstyr"}'),
  ('43.220', 'VVS-arbeid', 'Bygge- og anleggsvirksomhet', 'høyt', true,
   '{"SHA-plan","Dokumentert sikkerhetsopplæring for arbeidsutstyr"}'),
  ('43.910', 'Takarbeid', 'Bygge- og anleggsvirksomhet', 'svært høyt', true,
   '{"SHA-plan","Rutine for arbeid i høyden og fallsikring","HMS-kort"}'),
  ('49.410', 'Godstransport på vei', 'Transport og lagring', 'høyt', true,
   '{"Rutine for kjøre- og hviletid","Arbeidstidsoversikt for sjåfører"}'),
  ('49.320', 'Drosjebiltransport', 'Transport og lagring', 'middels', null,
   '{"Rutine ved vold og trusler","Rutine for alenearbeid"}'),
  ('52.100', 'Lagring', 'Transport og lagring', 'middels', null,
   '{"Dokumentert sikkerhetsopplæring for truck og løfteutstyr"}'),
  ('86.211', 'Allmenn legetjeneste', 'Helse- og sosialtjenester', 'middels', true,
   '{"Smittevernrutine","Rutine ved vold og trusler","Rutine ved stikkskade"}'),
  ('86.230', 'Tannhelsetjenester', 'Helse- og sosialtjenester', 'middels', true,
   '{"Smittevernrutine","Stoffkartotek for kjemikalier","Rutine ved stikkskade"}'),
  ('87.101', 'Somatiske spesialsykehjem', 'Helse- og sosialtjenester', 'høyt', true,
   '{"Smittevernrutine","Rutine ved vold og trusler","Rutine for forflytning og tunge løft"}'),
  ('81.210', 'Rengjøring av bygninger', 'Forretningsmessig tjenesteyting', 'høyt', true,
   '{"Offentlig godkjenning fra Arbeidstilsynet","HMS-kort for alle renholdere","Stoffkartotek for kjemikalier"}')
on conflict (nace_kode) do update set
  nace_navn        = excluded.nace_navn,
  nace_hovedgruppe = excluded.nace_hovedgruppe,
  risikonivaa      = excluded.risikonivaa,
  bht_paakrevd     = excluded.bht_paakrevd,
  dokumentkrav     = excluded.dokumentkrav;


insert into public.nace_forskriftskrav
  (nace_kode, forskrift_navn, forskrift_nummer, paragraf, krav, dokumenttype, kilde_url, verifisert_dato)
values
  -- ── Kontor, IT og rådgivning ──────────────────────────────────────────────
  ('62.010', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes ved planlegging, tilrettelegging og gjennomføring av arbeidet.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),
  ('62.010', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 8-1',
   'Arbeidstakerne skal ha nødvendig opplæring og øvelse i hensiktsmessig arbeidsteknikk.',
   'Opplæringsplan', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),
  ('62.010', 'Arbeidsplassforskriften', 'FOR-2011-12-06-1356', 'kapittel 2',
   'Arbeidsplass og arbeidslokale skal utformes og innredes slik at arbeidet kan utføres forsvarlig.',
   'Vernerunde', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1356', '2026-08-15'),

  ('70.220', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes ved planlegging, tilrettelegging og gjennomføring av arbeidet.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),
  ('70.220', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 8-1',
   'Arbeidstakerne skal ha nødvendig opplæring og øvelse i hensiktsmessig arbeidsteknikk.',
   'Opplæringsplan', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),
  ('70.220', 'Arbeidsplassforskriften', 'FOR-2011-12-06-1356', 'kapittel 2',
   'Arbeidsplass og arbeidslokale skal utformes og innredes slik at arbeidet kan utføres forsvarlig.',
   'Vernerunde', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1356', '2026-08-15'),

  -- ── Varehandel ────────────────────────────────────────────────────────────
  ('47.111', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 3A',
   'Særlige bestemmelser om vold og trussel om vold: risikoen skal kartlegges og arbeidstakerne ha opplæring og oppfølging.',
   'Rutine ved vold og trusler', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('47.111', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes, herunder ran- og voldsrisiko ved kundekontakt.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),
  ('47.111', 'Arbeidsplassforskriften', 'FOR-2011-12-06-1356', 'kapittel 2',
   'Arbeidslokalet skal utformes slik at manuell håndtering og varepåfylling kan skje forsvarlig.',
   'Vernerunde', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1356', '2026-08-15'),

  ('47.190', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 3A',
   'Særlige bestemmelser om vold og trussel om vold: risikoen skal kartlegges og arbeidstakerne ha opplæring og oppfølging.',
   'Rutine ved vold og trusler', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('47.190', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes, herunder ran- og voldsrisiko ved kundekontakt.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),
  ('47.190', 'Arbeidsplassforskriften', 'FOR-2011-12-06-1356', 'kapittel 2',
   'Arbeidslokalet skal utformes slik at manuell håndtering og varepåfylling kan skje forsvarlig.',
   'Vernerunde', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1356', '2026-08-15'),

  -- ── Servering ─────────────────────────────────────────────────────────────
  ('56.101', 'Næringsmiddelhygieneforskriften', 'FOR-2008-12-22-1623', 'forordning (EF) nr. 852/2004 artikkel 5',
   'Virksomheten skal innføre og gjennomføre faste rutiner basert på HACCP-prinsippene.',
   'HACCP-basert internkontroll', 'https://lovdata.no/dokument/SF/forskrift/2008-12-22-1623', '2026-08-15'),
  ('56.101', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 3A',
   'Vold og trussel om vold skal kartlegges — særlig ved kveldsarbeid og alkoholservering.',
   'Rutine ved vold og trusler', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('56.101', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes, herunder varme, glatte gulv og tidspress.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),

  ('56.102', 'Næringsmiddelhygieneforskriften', 'FOR-2008-12-22-1623', 'forordning (EF) nr. 852/2004 artikkel 5',
   'Virksomheten skal innføre og gjennomføre faste rutiner basert på HACCP-prinsippene.',
   'HACCP-basert internkontroll', 'https://lovdata.no/dokument/SF/forskrift/2008-12-22-1623', '2026-08-15'),
  ('56.102', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 3A',
   'Vold og trussel om vold skal kartlegges — særlig ved kveldsarbeid og alenearbeid.',
   'Rutine ved vold og trusler', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('56.102', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes, herunder varme, fett og glatte gulv.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),

  -- ── Bygg og anlegg ────────────────────────────────────────────────────────
  ('41.200', 'Byggherreforskriften', 'FOR-2009-08-03-1028', '§ 7',
   'Byggherren skal sørge for at det utarbeides en skriftlig plan for sikkerhet, helse og arbeidsmiljø (SHA-plan) før arbeidet starter.',
   'SHA-plan', 'https://lovdata.no/dokument/SF/forskrift/2009-08-03-1028', '2026-08-15'),
  ('41.200', 'Byggherreforskriften', 'FOR-2009-08-03-1028', '§ 8',
   'SHA-planen skal beskrive de konkrete risikoforholdene på plassen og tiltakene mot dem.',
   'SHA-plan', 'https://lovdata.no/dokument/SF/forskrift/2009-08-03-1028', '2026-08-15'),
  ('41.200', 'Byggherreforskriften', 'FOR-2009-08-03-1028', '§ 10',
   'Forhåndsmelding sendes Arbeidstilsynet før arbeid som varer mer enn 30 virkedager eller overstiger 500 dagsverk.',
   'Forhåndsmelding', 'https://lovdata.no/dokument/SF/forskrift/2009-08-03-1028', '2026-08-15'),
  ('41.200', 'Byggherreforskriften', 'FOR-2009-08-03-1028', '§ 15',
   'Det skal føres oversiktsliste over alle som utfører arbeid på bygge- eller anleggsplassen.',
   'Oversiktsliste', 'https://lovdata.no/dokument/SF/forskrift/2009-08-03-1028', '2026-08-15'),

  ('43.210', 'Byggherreforskriften', 'FOR-2009-08-03-1028', '§ 7',
   'Arbeid på bygge- eller anleggsplass skal omfattes av byggherrens SHA-plan.',
   'SHA-plan', 'https://lovdata.no/dokument/SF/forskrift/2009-08-03-1028', '2026-08-15'),
  ('43.210', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 17',
   'Arbeid i høyden skal planlegges og utføres med forsvarlig sikring mot fall.',
   'Rutine for arbeid i høyden', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('43.210', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', '§ 10-1',
   'Arbeidsutstyr som krever særlig forsiktighet ved bruk krever dokumentert sikkerhetsopplæring.',
   'Opplæringsbevis', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),

  ('43.220', 'Byggherreforskriften', 'FOR-2009-08-03-1028', '§ 7',
   'Arbeid på bygge- eller anleggsplass skal omfattes av byggherrens SHA-plan.',
   'SHA-plan', 'https://lovdata.no/dokument/SF/forskrift/2009-08-03-1028', '2026-08-15'),
  ('43.220', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 17',
   'Arbeid i høyden skal planlegges og utføres med forsvarlig sikring mot fall.',
   'Rutine for arbeid i høyden', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('43.220', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', '§ 10-1',
   'Arbeidsutstyr som krever særlig forsiktighet ved bruk krever dokumentert sikkerhetsopplæring.',
   'Opplæringsbevis', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),

  ('43.910', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 17',
   'Takarbeid er arbeid i høyden og skal ha forsvarlig fallsikring, planlagt før arbeidet starter.',
   'Rutine for arbeid i høyden', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('43.910', 'Byggherreforskriften', 'FOR-2009-08-03-1028', '§ 7',
   'Arbeid på bygge- eller anleggsplass skal omfattes av byggherrens SHA-plan.',
   'SHA-plan', 'https://lovdata.no/dokument/SF/forskrift/2009-08-03-1028', '2026-08-15'),
  ('43.910', 'Forskrift om HMS-kort på bygge- og anleggsplasser', 'FOR-2007-03-30-366', 'hele forskriften',
   'Alle som utfører arbeid på bygge- eller anleggsplass skal bære gyldig HMS-kort.',
   'HMS-kort', 'https://lovdata.no/nav/forskrift/2007-03-30-366', '2026-08-15'),

  -- ── Transport og lagring ──────────────────────────────────────────────────
  ('49.410', 'Forskrift om kjøre- og hviletid og fartsskriver for vegtransport i EØS', 'FOR-2007-07-02-877', 'hele forskriften',
   'Kjøre- og hviletid skal overholdes og registreres med fartsskriver.',
   'Rutine for kjøre- og hviletid', 'https://lovdata.no/dokument/SF/forskrift/2007-07-02-877', '2026-08-15'),
  ('49.410', 'Forskrift om arbeidstid for sjåfører og andre innenfor vegtransport', 'FOR-2005-06-10-543', 'hele forskriften',
   'Arbeidstiden for sjåfører skal registreres og holdes innenfor forskriftens rammer.',
   'Arbeidstidsoversikt', 'https://lovdata.no/dokument/SF/forskrift/2005-06-10-543', '2026-08-15'),
  ('49.410', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes, herunder lasting, sikring av last og alenekjøring.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),

  ('49.320', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 3A',
   'Vold og trussel om vold skal kartlegges — særlig ved nattkjøring og alenearbeid.',
   'Rutine ved vold og trusler', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('49.320', 'Forskrift om arbeidstid for sjåfører og andre innenfor vegtransport', 'FOR-2005-06-10-543', 'hele forskriften',
   'Arbeidstiden for sjåfører skal registreres og holdes innenfor forskriftens rammer.',
   'Arbeidstidsoversikt', 'https://lovdata.no/dokument/SF/forskrift/2005-06-10-543', '2026-08-15'),
  ('49.320', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes, herunder alenearbeid og uregelmessig arbeidstid.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),

  ('52.100', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', '§ 10-1',
   'Arbeidsutstyr som krever særlig forsiktighet ved bruk krever dokumentert sikkerhetsopplæring.',
   'Opplæringsbevis', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('52.100', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', '§ 10-3',
   'Truck, kran og masseforflytningsmaskiner krever sikkerhetsopplæring gitt av sertifisert opplæringsvirksomhet.',
   'Opplæringsbevis', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('52.100', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes, herunder truckkjøring, stabling og manuell håndtering.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),

  -- ── Helse og omsorg ───────────────────────────────────────────────────────
  ('86.211', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 6',
   'Arbeid som kan gi eksponering for biologiske faktorer skal risikovurderes, med tiltak mot smitte.',
   'Smittevernrutine', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('86.211', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 3A',
   'Vold og trussel om vold fra pasienter og pårørende skal kartlegges og forebygges.',
   'Rutine ved vold og trusler', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('86.211', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes, herunder smitterisiko og stikkskader.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),

  ('86.230', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 6',
   'Arbeid som kan gi eksponering for biologiske faktorer skal risikovurderes, med tiltak mot smitte.',
   'Smittevernrutine', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('86.230', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 3',
   'Kjemikalier i tannhelsearbeid skal kartlegges, og stoffkartotek skal være tilgjengelig.',
   'Stoffkartotek', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('86.230', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes, herunder smitte, kjemikalier og ensidig arbeidsstilling.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),

  ('87.101', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 6',
   'Arbeid som kan gi eksponering for biologiske faktorer skal risikovurderes, med tiltak mot smitte.',
   'Smittevernrutine', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('87.101', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 3A',
   'Vold og trussel om vold fra beboere skal kartlegges, og ansatte skal ha opplæring og oppfølging.',
   'Rutine ved vold og trusler', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15'),
  ('87.101', 'Forskrift om organisering, ledelse og medvirkning', 'FOR-2011-12-06-1355', '§ 7-1',
   'Arbeidsmiljøet skal kartlegges og risikovurderes, herunder forflytning, tunge løft og nattarbeid.',
   'Risikovurdering', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1355', '2026-08-15'),

  -- ── Renhold ───────────────────────────────────────────────────────────────
  ('81.210', 'Forskrift om offentlig godkjenning av renholdsvirksomheter', 'FOR-2012-05-08-408', 'kapittel 2',
   'Renholdsvirksomhet må være godkjent av Arbeidstilsynet for å kunne tilby renholdstjenester.',
   'Godkjenningsbevis', 'https://lovdata.no/dokument/SF/forskrift/2012-05-08-408', '2026-08-15'),
  ('81.210', 'Forskrift om offentlig godkjenning av renholdsvirksomheter', 'FOR-2012-05-08-408', 'kapittel 3',
   'Alle som utfører renholdsarbeid skal ha HMS-kort utstedt av kortutsteder utpekt av Arbeidstilsynet.',
   'HMS-kort', 'https://lovdata.no/dokument/SF/forskrift/2012-05-08-408', '2026-08-15'),
  ('81.210', 'Forskrift om utførelse av arbeid', 'FOR-2011-12-06-1357', 'kapittel 3',
   'Renholdskjemikalier skal kartlegges og risikovurderes, og stoffkartotek skal være tilgjengelig.',
   'Stoffkartotek', 'https://lovdata.no/dokument/SF/forskrift/2011-12-06-1357', '2026-08-15')
on conflict (nace_kode, forskrift_nummer, paragraf) do update set
  forskrift_navn  = excluded.forskrift_navn,
  krav            = excluded.krav,
  dokumenttype    = excluded.dokumenttype,
  kilde_url       = excluded.kilde_url,
  verifisert_dato = excluded.verifisert_dato;
