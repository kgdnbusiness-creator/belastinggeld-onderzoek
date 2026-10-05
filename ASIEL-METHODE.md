# Asiel en migratie: afbakening en aansluiting

Versie 1, gecontroleerd op 2 oktober 2026. De nieuwe tab `Asiel & migratie` beantwoordt welke posten in het belangrijkste migratieartikel staan en of benoemde bijdragen aan COA, IND en VluchtelingenWerk numeriek aansluiten op de gepubliceerde ontvangersbron.

## Afbakening

| Jaar | Begrotingshoofdstuk | Artikel |
|---|---|---|
| 2023–2024 | VI, Justitie en Veiligheid | 37, Migratie |
| 2025–2026 | XX, Asiel en Migratie | 37, Asiel en Migratie |

Deze mapping staat expliciet in `pipeline_asylum.py`. Nieuwe jaren worden niet zonder validatie toegevoegd. Een ontbrekend of dubbel geselecteerd artikel stopt het bouwen. Oude nulregels in andere hoofdstukken worden niet opnieuw in het artikelbudget geteld.

Artikel 37 omvat meer dan asiel. De IND-bijdrage betreft ook reguliere migratie en naturalisatie. Oekraïense ontheemden worden als aparte groep getoond. Het resterende bedrag heet overige migratieposten; het wordt niet automatisch aan asiel toegerekend. Alle groepsdetails zijn uitklapbaar, met bronbestand, IBOS en bronregel. Er is een export van alle geselecteerde artikelposten.

De groepen vormen een verdeling van de detailposten. Het gerapporteerde artikeltotaal blijft apart leidend. Een afwijking tussen totaal en detail blijft zichtbaar. Deze bedragen vormen geen volledig geconsolideerd totaal van Nederlandse asieluitgaven: andere begrotingsartikelen, gemeenten en uiteindelijke leveranciers zijn niet volledig in beeld.

## Vergelijking per organisatie

De organisatievergelijking omvat alle exact herkende Rijksbegrotingsposten, inclusief posten buiten het geselecteerde artikel. De ontvangersbron kent immers een andere afbakening. Posten buiten het artikel zijn afzonderlijk uitklapbaar. De historische naam `Vluchtelingenwerk Nederland (VWN)` is toegevoegd; IND en de volledige naam Immigratie- en Naturalisatiedienst vormen één expliciete naamgroep. Substrings zoals INDustrie worden niet gekoppeld.

Het verschil is **ontvangersbron minus benoemde Rijksbegrotingsposten**. Het wordt alleen berekend voor twee beschikbare realisaties van hetzelfde jaar. Een ontbrekende bron is `null`, niet nul. De ontvangersbron wordt niet bij het artikelbudget opgeteld.

| Organisatie, realisatie 2025 | Benoemde Rijksbegrotingsposten | Ontvangersbron | Verschil |
|---|---:|---:|---:|
| COA | € 3.626.266.000 | € 4.001.907.000 | € 375.641.000 |
| IND | € 1.017.282.000 | € 1.017.282.000 | € 0 |
| VluchtelingenWerk Nederland | € 22.228.000 | € 27.284.000 | € 5.056.000 |

De IND sluit numeriek aan, maar daarmee is geen transactie- of KvK-koppeling bewezen. De andere verschillen blijven onverklaard; mogelijke afbakenings- en afrekeningsverschillen zijn onderzoeksvragen, geen vastgestelde oorzaken. Geanonimiseerde ontvangers worden niet op basis van vermoedens aan een organisatie gekoppeld. Dit overzicht is niet gelijk aan de jaarrekening of totale omzet van een organisatie.

## Bronnen en volgende controle

- [Jaarverslag 2025 Asiel en Migratie](https://www.rijksfinancien.nl/jaarverslag/2025/XX): beleidsmatige context; reguliere migratie, Oekraïne en afrekeningen zijn afzonderlijke onderwerpen.
- [Jaarverslag 2024 Justitie en Veiligheid](https://www.rijksfinancien.nl/jaarverslag/2024/VI): historische indeling.
- [Budgettaire tabel artikel 37, 2025](https://www.rijksfinancien.nl/jaarverslag/U/2025/XX/37): detailbedragen in duizenden euro’s.
- [Ontvangers 2025](https://www.rijksfinancien.nl/open-data/api/json/financiele_instrumenten?year%5B%5D=2025): bedragen al in euro’s; gepubliceerde namen en beperkte dekking.

Om verschillen daadwerkelijk te verklaren, moeten subsidie- en bijdrageafrekeningen en organisatiejaarrekeningen worden gekoppeld aan dezelfde verslagperiode en grondslag. Ontvangsten/terugbetalingen worden niet automatisch afgetrokken. ODA-toerekening is geen extra betaling en mag niet bovenop de bijdragen worden opgeteld.

## Verificatie

18 Python-tests geslaagd, inclusief afbakening, bijdragen buiten het artikel, ontbrekende gegevens, ramingen, onbekende jaren en historische namen. JavaScript-syntax gecontroleerd. Online bouw 2023–2026 geslaagd. De detailposten van artikel 37 sluiten in deze vier snapshots exact aan op het artikeltotaal. In Chrome zijn 2025 en 2026 gecontroleerd; bij 2026 staan ontvangers en verschillen als niet beschikbaar.
