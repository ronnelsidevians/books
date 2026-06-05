#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import argparse, json, re, unicodedata

ROOT = Path(__file__).resolve().parent
BOOKS = ROOT / 'books'
DATA = ROOT / 'data'
COVERS = ROOT / 'covers'
TR = {'а':'a','б':'b','в':'v','г':'h','ґ':'g','д':'d','е':'e','є':'ie','ж':'zh','з':'z','и':'y','і':'i','ї':'i','й':'i','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ь':'','ю':'iu','я':'ia','ы':'y','э':'e','ъ':'','ё':'yo'}
ICON_NAMES = ('icon.png', 'icon.jpg', 'icon.jpeg')

def slug(s):
    s = ''.join(TR.get(c, c) for c in str(s).lower())
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-') or 'book'

def parse(pdf):
    rel = pdf.relative_to(BOOKS)
    title = pdf.stem.strip()
    folder = '' if rel.parent.as_posix() == '.' else rel.parent.as_posix()
    order = None
    m = re.match(r'^\s*(\d+)[\s._\-–—]+(.+)$', title)
    if m:
        order = int(m.group(1))
        title = m.group(2).strip()
    return folder, order, title

def fallback_cover(out, title):
    from PIL import Image, ImageDraw, ImageFont
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGB', (720, 780), (250, 204, 21))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 90, 780], fill=(146, 64, 14))
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 48)
    except Exception:
        font = None
    d.multiline_text((130, 250), title[:90], fill=(15, 23, 42), font=font, spacing=10)
    img.save(out, 'JPEG', quality=88)

def cover(pdf, out, zoom=2.0):
    try:
        import fitz
        from PIL import Image
        out.parent.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(str(pdf))
        page = doc.load_page(0)
        r = page.rect
        clip = fitz.Rect(r.x0 + r.width / 2, r.y0, r.x1, r.y1)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False)
        img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        w, h = img.size
        img = img.crop((0, 0, w, int(h * 0.78)))
        target = 0.82
        w, h = img.size
        if h and w / h < target:
            nh = int(w / target)
            img = img.crop((0, 0, w, min(h, nh)))
        if img.width > 760:
            nh = int(img.height * (760 / img.width))
            img = img.resize((760, nh), Image.LANCZOS)
        img.save(out, 'JPEG', quality=88, optimize=True)
        return True
    except Exception as e:
        print('Cover fallback:', pdf.relative_to(BOOKS), e)
        fallback_cover(out, pdf.stem)
        return True

def make_collage(folder_name, cover_paths, out):
    from PIL import Image, ImageDraw, ImageFont
    out.parent.mkdir(parents=True, exist_ok=True)
    W, H = 720, 780
    img = Image.new('RGB', (W, H), (245, 239, 222))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], outline=(20, 20, 20), width=10)
    slots = [(36,42,342,340), (378,42,684,340), (36,370,342,668), (378,370,684,668)]
    for i, slot in enumerate(slots):
        ok = False
        if i < len(cover_paths) and Path(cover_paths[i]).exists():
            try:
                c = Image.open(cover_paths[i]).convert('RGB')
                c.thumbnail((slot[2]-slot[0], slot[3]-slot[1]))
                x = slot[0] + ((slot[2]-slot[0])-c.width)//2
                y = slot[1]
                img.paste(c, (x, y))
                ok = True
            except Exception:
                ok = False
        if not ok:
            d.rectangle(slot, fill=(230,220,200), outline=(20,20,20), width=4)
        else:
            d.rectangle(slot, outline=(20,20,20), width=4)
    d.rectangle([0, H-82, W, H], fill=(20,20,20))
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34)
    except Exception:
        font = None
    d.text((30, H-60), folder_name[:32], fill=(245,239,222), font=font)
    img.save(out, 'JPEG', quality=88, optimize=True)

def folder_icon(folder):
    if not folder.exists() or not folder.is_dir():
        return None
    files = {p.name.lower(): p for p in folder.iterdir() if p.is_file()}
    for name in ICON_NAMES:
        if name in files:
            return files[name]
    return None

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--title', default='Книги Марка і Давида')
    p.add_argument('--author', default='Oleksandr Ryzhkov')
    p.add_argument('--category', default='PDF')
    p.add_argument('--cover-zoom', type=float, default=2.0)
    a = p.parse_args()
    BOOKS.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    COVERS.mkdir(exist_ok=True)

    pdfs = sorted(
        [x for x in BOOKS.rglob('*') if x.is_file() and x.suffix.lower() == '.pdf' and not any(part.startswith('.') for part in x.relative_to(BOOKS).parts)],
        key=lambda x: x.relative_to(BOOKS).as_posix().lower()
    )

    used = set()
    books = []
    by_folder = {}
    all_folders = set()

    for pdf in pdfs:
        folder, order, title = parse(pdf)
        if folder:
            parts = folder.split('/')
            for i in range(1, len(parts) + 1):
                all_folders.add('/'.join(parts[:i]))
        base = slug((folder + '-' if folder else '') + title)
        ident = base
        i = 2
        while ident in used:
            ident = f'{base}-{i}'
            i += 1
        used.add(ident)
        cf = COVERS / f'{ident}.jpg'
        cover(pdf, cf, a.cover_zoom)
        # Raw path. app.js encodes once. This keeps Cyrillic paths working.
        rel = 'books/' + '/'.join(pdf.relative_to(BOOKS).parts)
        item = {'id': ident, 'title': title, 'author': a.author, 'category': a.category, 'file': rel, 'cover': 'covers/' + cf.name, 'series': folder, 'order': order, 'tags': []}
        books.append(item)
        if folder:
            by_folder.setdefault(folder, []).append(item)

    # Physical folders are included even if they only contain subfolders or icon.*.
    for d in sorted([x for x in BOOKS.rglob('*') if x.is_dir() and not any(part.startswith('.') for part in x.relative_to(BOOKS).parts)], key=lambda x: x.relative_to(BOOKS).as_posix().lower()):
        rel = d.relative_to(BOOKS).as_posix()
        if rel and rel != '.':
            all_folders.add(rel)
            parts = rel.split('/')
            for i in range(1, len(parts)):
                all_folders.add('/'.join(parts[:i]))

    books.sort(key=lambda b: (b.get('series') or 'яяя', b.get('order') if b.get('order') is not None else 999999, b['title'].lower()))

    def descendant_books(folder):
        prefix = folder + '/'
        return [b for b in books if b.get('series') == folder or b.get('series', '').startswith(prefix)]

    series_list = []
    for folder in sorted(all_folders, key=lambda x: (x.count('/'), x.lower())):
        direct = sorted(by_folder.get(folder, []), key=lambda b: (b.get('order') if b.get('order') is not None else 999999, b['title'].lower()))
        desc = descendant_books(folder)
        parent = Path(folder).parent.as_posix()
        if parent == '.':
            parent = ''
        title = Path(folder).name
        icon = folder_icon(BOOKS / folder)
        if icon:
            cover_url = 'books/' + '/'.join(icon.relative_to(BOOKS).parts)
            cover_source = 'icon'
        else:
            collage = COVERS / (slug(folder) + '-series.jpg')
            make_collage(title, [ROOT / b['cover'] for b in desc[:4]], collage)
            cover_url = 'covers/' + collage.name
            cover_source = 'collage'
        series_list.append({
            'id': slug(folder),
            'title': title,
            'path': folder,
            'parent': parent,
            'cover': cover_url,
            'coverSource': cover_source,
            'count': len(desc),
            'bookIds': [b['id'] for b in desc],
            'directBookIds': [b['id'] for b in direct]
        })

    (DATA / 'books.json').write_text(json.dumps({'title': a.title, 'books': books, 'series': series_list}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'PDF found: {len(books)}')
    print(f'Folders found: {len(series_list)}')
    print('Generated data/books.json')

if __name__ == '__main__':
    main()
