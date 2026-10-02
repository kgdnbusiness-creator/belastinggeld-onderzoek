"""Official source discovery and reproducible downloads (standard library only)."""
import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

BASE = 'https://www.rijksfinancien.nl'
CATALOG = BASE + '/overzicht-datasets'
LEGACY_CATALOG = BASE + '/open-data/budgettaire%20tabellen%20rijksbegroting'
RECIPIENT_API = BASE + '/open-data/api/json/financiele_instrumenten'
RECIPIENT_YEARS = BASE + '/open-data/api/json/v2/financiele_instrumenten/available_years'
PHASES = {'OW': 'OWB', 'OWB': 'OWB', 'O1': 'O1', 'I1': 'O1',
          'SBS': 'SBS', 'I2': 'SBS', 'O2': 'O2', 'JV': 'JV'}
RANK = {'OWB': 1, 'O1': 2, 'SBS': 3, 'O2': 4, 'JV': 5}


class DataError(ValueError):
    """A source cannot be safely interpreted; do not publish."""


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.urls.extend(v for k, v in attrs if k == 'href' and v)


def phase_of(name):
    match = re.search(r'[_ /](OWB|OW|O1|I1|SBS|I2|O2|JV)[_ .]', unquote(name))
    return PHASES.get(match.group(1)) if match else None


def source_record(url, data, **extra):
    return {'url': url, 'sha256': hashlib.sha256(data).hexdigest(),
            'bytes': len(data), **extra}


def download(url, cache, refresh=False):
    """Only official HTTPS endpoints. Cached bytes are immutable for this run."""
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in {'www.rijksfinancien.nl', 'rijksfinancien.nl'}:
        raise DataError(f'Niet-officiële bron-URL: {url}')
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / hashlib.sha256(url.encode()).hexdigest()
    if not refresh and target.exists() and time.time() - target.stat().st_mtime < 86400:
        return target.read_bytes()
    request = urllib.request.Request(url, headers={'User-Agent': 'belastinggeld-onderzoek/0.2'})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if urlparse(response.url).hostname not in {'www.rijksfinancien.nl', 'rijksfinancien.nl'}:
                    raise DataError('Onverwachte redirect buiten Rijksfinanciën')
                data = response.read()
            if not data:
                raise DataError(f'Leeg bronbestand: {url}')
            target.write_bytes(data)
            return data
        except (OSError, TimeoutError) as exc:
            last = exc
            if attempt < 2:
                time.sleep(attempt + 1)
    raise DataError(f'Download mislukt: {url}: {last}')


def archive_csv(data, source_url, cache):
    """Read selected members to stdout: no archive paths are extracted to disk."""
    executable = shutil.which('bsdtar') or shutil.which('tar')
    if not executable:
        raise DataError('Voor jaararchieven is bsdtar nodig (Linux: libarchive-tools; Windows: tar).')
    archive = Path(cache) / (hashlib.sha256(data).hexdigest() + '.7z')
    archive.write_bytes(data)
    listing = subprocess.run([executable, '-tf', str(archive)], capture_output=True, check=False)
    if listing.returncode:
        raise DataError('Kan jaararchief niet lezen; installeer libarchive-tools/bsdtar.')
    names = listing.stdout.decode('utf-8').splitlines()
    candidates = [n for n in names if n.lower().endswith('_excl.csv') and phase_of(n)]
    if not candidates:
        raise DataError(f'Geen bestand exclusief premies in {source_url}; dekking niet stilzwijgend wijzigen.')
    phase = max((phase_of(n) for n in candidates), key=RANK.get)
    selected = [n for n in candidates if phase_of(n) == phase]
    if len(selected) != 1:
        raise DataError(f'Ambigue bronversies in {source_url}: {selected}')
    name = selected[0]
    if name.startswith(('/', '-')) or '..' in Path(name).parts:
        raise DataError('Onveilig archiefpad')
    result = subprocess.run([executable, '-xOf', str(archive), name], capture_output=True, check=False)
    if result.returncode or not result.stdout:
        raise DataError(f'Kan {name} niet uit jaararchief lezen')
    return name, phase, result.stdout


def discover(years, cache, refresh=False):
    """Select one complete snapshot per year, preferring final annual reports."""
    urls = set()
    # Both official catalogues are needed: the newer catalogue archives closed years.
    for catalog in (CATALOG, LEGACY_CATALOG):
        parser = Links()
        parser.feed(download(catalog, cache, refresh).decode('utf-8-sig'))
        urls.update(urljoin(catalog, u) for u in parser.urls)
    snapshots = []
    for year in years:
        if year < 2023:
            raise DataError(f'{year}: historische bestanden hebben een andere/onvolledig gevalideerde dekking. '
                            'Gebruik --years 2023-...; oude jaren worden niet als nul gepubliceerd.')
        candidates = [u for u in urls if f'_{year}_' in u and u.lower().endswith('_excl.csv') and phase_of(u)]
        archives = [u for u in urls if re.search(fr'Budgettaire_Tabellen_{year}\.7z$', u)]
        # Closed-year archive is authoritative if a JV CSV is absent from the catalogue.
        if archives and not any(phase_of(u) == 'JV' for u in candidates):
            if len(archives) != 1:
                raise DataError(f'Meerdere jaararchieven voor {year}')
            url = archives[0]
            packed = download(url, cache, refresh)
            member, phase, data = archive_csv(packed, url, cache)
            record = source_record(url, data, jaar=year, fase=phase, archiefbestand=member,
                                   archief_sha256=hashlib.sha256(packed).hexdigest())
        else:
            if not candidates:
                raise DataError(f'Geen bron exclusief premies voor verwacht jaar {year}')
            phase = max((phase_of(u) for u in candidates), key=RANK.get)
            selected = sorted(u for u in candidates if phase_of(u) == phase)
            if len(selected) != 1:
                raise DataError(f'Meerdere bronversies voor {year} {phase}: {selected}')
            url = selected[0]
            data = download(url, cache, refresh)
            record = source_record(url, data, jaar=year, fase=phase)
        snapshots.append((data, record))
    return snapshots


def local_sources(folder, years):
    snapshots = []
    for path in sorted(Path(folder).rglob('*.csv')):
        if 'incl' in path.name.lower():
            continue
        match = re.search(r'(20\d\d)', path.name)
        phase = phase_of(path.name)
        if not match or not phase or int(match.group(1)) not in years:
            continue
        data = path.read_bytes()
        snapshots.append((data, source_record(path.name, data, jaar=int(match.group(1)), fase=phase)))
    return snapshots
