#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build static GitHub Pages PDF PWA.
Scans /books/*.pdf and injects metadata into template.html.
Compatible with: python build_library.py --out dist --title "..."
"""
from pathlib import Path
import argparse, json, html, re, unicodedata, shutil

ROOT = Path(__file__).resolve().parent
BOOKS_DIR = ROOT / "books"
TEMPLATE = ROOT / "template.html"

TR = {
    'а':'a','б':'b','в':'v','г':'h','ґ':'g','д':'d','е':'e','є':'ie','ж':'zh','з':'z','и':'y','і':'i','ї':'i','й':'i',
    'к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch',
    'ш':'sh','щ':'shch','ь':'','ю':'iu','я':'ia','ы':'y','э':'e','ъ':'','ё':'yo'
}

def slug(text: str) -> str:
    text = ''.join(TR.get(ch, ch) for ch in text.lower())
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text or 'book'

def scan_books():
    BOOKS_DIR.mkdir(exist_ok=True)
    pdfs = sorted(list(BOOKS_DIR.glob('*.pdf')) + list(BOOKS_DIR.glob('*.PDF')), key=lambda p: p.name.lower())
    used = set()
    books = []
    for pdf in pdfs:
        title = pdf.stem.strip()
        base = slug(title)
        ident = base
        i = 2
        while ident in used:
            ident = f'{base}-{i}'
            i += 1
        used.add(ident)
        books.append({
            'id': ident,
            'title': title,
            'file': 'books/' + pdf.name,
            'category': 'PDF',
            'tags': []
        })
    return books

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='dist')
    parser.add_argument('--title', default='Моя PDF-бібліотека')
    args = parser.parse_args()

    out = ROOT / args.out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    books = scan_books()
    data = json.dumps(books, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

    if not TEMPLATE.exists():
        raise FileNotFoundError('template.html not found in repository root')

    result = TEMPLATE.read_text(encoding='utf-8')
    result = result.replace('__TITLE__', html.escape(args.title)).replace('__BOOKS__', data)

    (out / 'index.html').write_text(result, encoding='utf-8')
    (ROOT / 'index.html').write_text(result, encoding='utf-8')
    (out / '.nojekyll').write_text('', encoding='utf-8')

    for name in ['manifest.webmanifest', 'sw.js']:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, out / name)

    if (ROOT / 'icons').exists():
        shutil.copytree(ROOT / 'icons', out / 'icons', dirs_exist_ok=True)
    if BOOKS_DIR.exists():
        shutil.copytree(BOOKS_DIR, out / 'books', dirs_exist_ok=True)

    print(f'Built {out}/index.html')
    print(f'Books found: {len(books)}')

if __name__ == '__main__':
    main()
