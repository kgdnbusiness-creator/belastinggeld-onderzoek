# Controle en implementatie, 2 oktober 2026

## Gevonden en hersteld

- De oude ontdekking sloeg ontbrekende jaren over. Nu komt één volledige, hoogste beschikbare begrotingsfase per gevraagd jaar uit de officiële catalogi. Ontbrekende jaren, onbekende kolommen, dubbele IBOS-codes en conflicterende versies stoppen publicatie.
- De 2026 SBS-bron bevat `StandSBS`. De oude pipeline gebruikte `StandO1` maar vermeldde fase SBS. De bedragkolom volgt nu expliciet de fase.
- Nul is een geldige code. Hiërarchische diepte volgt IBOS, waardoor 2023 en terminale instrumentregels behouden blijven.
- De wereldwijde top-200-filter verwijderde kleine posten voordat gebruikers konden zoeken. Alle detailposten blijven nu in de dataset en CSV-export. Alleen de schermweergave heeft een limiet.
- Totalen worden niet samen met hun onderliggende posten opgeteld. Gerapporteerde totalen blijven leidend; aansluitverschillen zijn zichtbaar en worden niet weggepoetst. V, U en O blijven gescheiden.
- Herkomst bevat bestand, SHA-256, fase, bedragkolom, IBOS en bronregel. Ingesloten JSON en CSV-export krijgen bescherming tegen script- en formule-injectie.

## Organisaties aansluiten

De officiële financiële-instrumenten-API bevat ontvangers en hun gerealiseerde bedragen per jaar. De bedragen zijn al euro’s, anders dan de begrotings-CSV. De nieuwe tab Organisaties toont beide bronbeelden apart. Er is bewust geen optelling tussen beide.

COA en VluchtelingenWerk zijn via een expliciete namenlijst herkenbaar. Dat is een beperkte naamkoppeling, geen bewezen transactie- of KvK-koppeling. Andere gepubliceerde ontvangers zijn doorzoekbaar. De bron dekt niet alle overheidsbetalingen. Ontbrekende jaren/ontvangers zijn geen nulbedragen.

Bijvoorbeeld 2025: COA heeft € 3.593.266.000 onder Asiel en Migratie én € 33.000.000 onder Justitie en Veiligheid. VluchtelingenWerk heeft € 21.052.000 onder Asiel en Migratie én € 1.176.000 onder SZW. Een zoekfilter op één ministerie zou geldstromen missen.

EU heeft een eigen uitsplitsing van artikel 3 van Buitenlandse Zaken: afdrachten en ontvangsten afzonderlijk, met Raad van Europa/Benelux herkenbaar als andere organisaties. Deze selectie is geen complete netto EU-positie van Nederland.

## Grenzen en vervolgstappen

1. Historische jaren 2021–2022 ontbreken expliciet. De oude bestanden hebben afwijkende indeling/dekking, waaronder uitsluitend inclusief premies voor 2022. Een aparte historische adapter moet eerst tegen jaarverslagen worden gevalideerd.
2. De bron bevat aansluitverschillen. Op de gecontroleerde 2023–2026-bestanden zijn 11 verschillen boven de afrondingstolerantie zichtbaar, ook bij ontvangsten. Voor zover beschikbaar blijft het gerapporteerde artikeltotaal leidend. Detailregels mogen daarom niet zonder verdere controle tot een nieuw totaal worden opgeteld.
3. Een volledige geldstroomgrafiek vereist ontvangeridentificatie (bijvoorbeeld KvK), stabiele beleidsartikelcodes en documentatie van doorbetalingen. Niet alleen op een naam of gelijk bedrag koppelen.
4. Klimaat, asiel en defensie vragen een versieerbare thematoedeling per jaar/artikel/post. Thema’s kunnen overlappen: Europese Vredesfaciliteit raakt bijvoorbeeld EU én defensie. Gebruik expliciete overlapregels voordat thematotalen worden gepubliceerd.
5. EU uitbreiden met ontvangsten buiten de rijksbegroting, directe EU-subsidies en een duidelijk beschreven definitie van netto afdrachten. Publieke jaarstukken van COA/VluchtelingenWerk dienen als aanvullende controle, niet als extra bedragen bovenop Rijksbijdragen.
6. Gemeenten, provincies en premiegefinancierde uitgaven blijven buiten deze eerste bron. De schakelaar voor doorstortingen is indicatief en geen volledige consolidatie.

## Verificatie

`python -m unittest -v` test fasekeuze, nulcodes, terminale instrumenten, volledige zoekdekking, ontbrekende jaren, dubbele/conflicterende bronversies, ongeldige bedragen, bronverschillen, ontvangers-eenheden en veilige JSON-inbedding.

`python pipeline.py --years 2023-2026` is uitgevoerd met de officiële online catalogi, jaarverslagbestanden, de 2026 SBS-CSV en de ontvangers-API. Resultaat: 11.097 doorzoekbare begrotingsposten, 92.072 ontvangerregels over 2023–2025. Ontvangers voor 2026 waren niet beschikbaar en worden als zodanig getoond.

Bronnen: [datasets](https://www.rijksfinancien.nl/overzicht-datasets), [begrotingstabellen](https://www.rijksfinancien.nl/open-data/budgettaire%20tabellen%20rijksbegroting), [API-documentatie](https://www.rijksfinancien.nl/open-data/api-documentatie).
