# Belastinggeld-pipeline

Haalt de Budgettaire Tabellen van de Rijksbegroting (Min. van Financiën, CC-0) op,
telt uitgaven per hoofdstuk/artikel/instrument/regeling op, signaleert grote veranderingen
en bouwt `site/index.html` (één bestand, data ingebed).

## Gebruik
    python pipeline.py --years 2021-2026     # internet nodig (data.overheid.nl, rijksfinancien.nl)
    python pipeline.py --local ./csv         # of met zelf gedownloade CSV's
Open daarna `site/index.html`, of publiceer de map `site/` (GitHub Pages; workflow meegeleverd).

## Methode
- Alleen `VUO = U` (uitgaven). V en O niet optellen.
- Artikeltotaal: `Totaal=J`, geen artikelonderdeel/instrument. Instrument: `Totaal=J`, instrument gevuld, geen detail.
  Regeling: `Totaal=N` met detail. Zo ontstaat geen dubbeltelling.
- Bedragen in de bron zijn x € 1.000. Per jaar de hoogste beschikbare fase (JV > O2 > SBS > O1 > OW).
- Controle: instrumenten moeten optellen tot het artikeltotaal; afwijkingen komen onder "Methode".
- Doorgesluisde bijdragen tussen hoofdstukken (bijv. naar Mobiliteitsfonds) tellen dubbel; aparte schakelaar "netto".

## Beperkingen
Alleen Rijk, exclusief premies; geen gemeenten/provincies (volgende bron: CBS/Iv3).
Het workflow-bestand en de datasetlink-detectie zijn niet tegen de live sites getest.
