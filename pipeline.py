#!/usr/bin/env python3
"""Build only after all requested budget years have passed structural validation."""
import argparse
import datetime as dt
import json
from pathlib import Path
from pipeline_sources import DataError, discover, local_sources
from pipeline_model import build
from pipeline_organisations import enrich
from pipeline_asylum import build_asylum

ROOT = Path(__file__).parent


def render(data):
    template = (ROOT / 'site/template.html').read_text(encoding='utf-8')
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    html = template.replace('/*__DATA__*/null', payload)
    extension = (ROOT / 'dashboard-extra.js').read_text(encoding='utf-8')
    extension += '\n' + (ROOT / 'dashboard-asiel.js').read_text(encoding='utf-8')
    html = html.replace('</script>', '\n' + extension + '\n</script>')
    if '/*__DATA__*/null' not in template:
        raise DataError('Datamarker ontbreekt in template')
    return html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', default=f'2023-{dt.date.today().year}')
    parser.add_argument('--local', help='Recursieve map met CSV-bronnen; ontvangers offline niet geladen')
    parser.add_argument('--cache', default=str(ROOT / '.cache'))
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    lo, hi = map(int, args.years.split('-'))
    if not 2023 <= lo <= hi <= dt.date.today().year + 1:
        raise DataError('Gebruik een jaarrange vanaf 2023; historische dekking is nog niet gevalideerd')
    years = list(range(lo, hi + 1))
    snapshots = local_sources(args.local, years) if args.local else discover(years, args.cache, args.refresh)
    data = build(snapshots, years)
    data['gegenereerd'] = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    enrich(data, args.cache, offline=bool(args.local), refresh=args.refresh)
    build_asylum(data)
    html = render(data)
    for path, content in ((ROOT / 'data/uitgaven.json', json.dumps(data, ensure_ascii=False, indent=1)),
                          (ROOT / 'site/index.html', html)):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(path)
    print(f'Gebouwd: {len(years)} jaren, {len(data["grootste_regelingen"])} doorzoekbare posten, {len(data["controle"])} zichtbare bronverschillen')


if __name__ == '__main__':
    try:
        main()
    except (DataError, UnicodeError, ValueError) as exc:
        raise SystemExit(f'Publicatie gestopt: {exc}') from exc
