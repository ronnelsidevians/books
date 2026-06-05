#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Books PWA library builder.

Що вміє:
- рекурсивно сканує books/** для підтримки папка-в-папці;
- для зображення папки першочергово використовує books/<папка>/icon.png або icon.jpg/icon.jpeg;
- якщо icon.* у папці немає — створює поточний fallback: колаж з перших 4 обкладинок книг у цій папці та її підпапках;
- генерує data/library.json та covers/** для app.js.

Запуск:
    python build_library.py
    python build_library.py --out dist --title "PDF Library"
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
import argparse
import hashlib
import json
import re
import shutil
import unicodedata
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
BOOKS = ROOT / "books"
DATA = ROOT / "data"
COVERS = ROOT / "covers"

TR = {
    'а':'a','б':'b','в':'v','г':'h','ґ':'g','д':'d','е':'e','є':'ie','ж':'zh','з':'z','и':'y','і':'i','ї':'i','й':'i',
    'к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch',
    'ш':'sh','щ':'shch','ь':'','ю':'iu','я':'ia','ы':'y','э':'e','ъ':'','ё':'yo'
}
ICON_NAMES = ("icon.png", "icon.jpg", "icon.jpeg")
PDF_EXTS = {".pdf"}


def slug(text: str) -> str:
    text = ''.join(TR.get(ch, ch) for ch in text.lower())
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-') or 'item'


def posix_rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def url_join(*parts: str) -> str:
    return '/'.join(quote(str(p).strip('/'), safe='') for p in parts if str(p).strip('/'))


def is_hidden(path: Path) -> bool:
    return any(part.startswith('.') for part in path.parts)


def parse_book_title(pdf: Path) -> tuple[int | None, str]:
    title = pdf.stem.strip()
    order = None
    m = re.match(r'^\s*(\d+)[\s._\-–—]+(.+)$', title)
    if m:
        order = int(m.group(1))
        title = m.group(2).strip()
    return order, title


def fallback_cover(out: Path, title: str, kind: str = "book") -> None:
    from PIL import Image, ImageDraw, ImageFont
    W, H = 720, 780
    bg = (250, 204, 21) if kind == "book" else (245, 239, 222)
    spine = (146, 64, 14) if kind == "book" else (37, 99, 235)
    img = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 92, H], fill=spine)
    d.rectangle([0, 0, W-1, H-1], outline=(15, 23, 42), width=8)
    try:
        font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 54)
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
    except Exception:
        font_big = font_small = None
    label = "Папка" if kind == "folder" else "Книга"
    d.text((130, 120), label, fill=(15, 23, 42), font=font_small)
    words = title[:120]
    d.multiline_text((130, 245), words, fill=(15, 23, 42), font=font_big, spacing=12)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, 'JPEG', quality=88, optimize=True)


def make_pdf_cover(pdf: Path, out: Path, zoom: float = 2.0) -> bool:
    try:
        import fitz  # PyMuPDF
        from PIL import Image
        doc = fitz.open(str(pdf))
        page = doc.load_page(0)
        r = page.rect
        # Як у поточній версії: беремо праву частину першої сторінки, обрізаємо низ.
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
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out, 'JPEG', quality=88, optimize=True)
        return True
    except Exception as e:
        print('Cover fallback:', pdf.relative_to(ROOT), e)
        fallback_cover(out, pdf.stem, "book")
        return True


def make_collage(title: str, cover_files: list[Path], out: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont
    W, H = 720, 780
    img = Image.new('RGB', (W, H), (245, 239, 222))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, H - 1], outline=(20, 20, 20), width=10)
    slots = [(36, 42, 342, 340), (378, 42, 684, 340), (36, 370, 342, 668), (378, 370, 684, 668)]
    used = 0
    for i, slot in enumerate(slots):
        if i >= len(cover_files):
            break
        cp = cover_files[i]
        if not cp.exists():
            continue
        try:
            c = Image.open(cp).convert('RGB')
            c.thumbnail((slot[2] - slot[0], slot[3] - slot[1]))
            x = slot[0] + ((slot[2] - slot[0]) - c.width) // 2
            y = slot[1] + ((slot[3] - slot[1]) - c.height) // 2
            img.paste(c, (x, y))
            d.rectangle(slot, outline=(20, 20, 20), width=4)
            used += 1
        except Exception:
            continue
    if used == 0:
        fallback_cover(out, title, "folder")
        return
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34)
    except Exception:
        font = None
    d.rounded_rectangle([36, 690, 684, 758], radius=22, fill=(255, 255, 255), outline=(20, 20, 20), width=3)
    d.text((62, 708), title[:42], fill=(15, 23, 42), font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, 'JPEG', quality=88, optimize=True)


def find_folder_icon(folder: Path) -> Path | None:
    if not folder.exists() or not folder.is_dir():
        return None
    # Пріоритет: icon.png -> icon.jpg -> icon.jpeg, без урахування регістру.
    lower_map = {p.name.lower(): p for p in folder.iterdir() if p.is_file()}
    for name in ICON_NAMES:
        if name in lower_map:
            return lower_map[name]
    return None


def cover_output_for_pdf(pdf: Path) -> Path:
    rel = pdf.relative_to(BOOKS)
    parent = rel.parent
    base = slug(pdf.stem) + '-' + hashlib.sha1(rel.as_posix().encode('utf-8')).hexdigest()[:8] + '.jpg'
    return COVERS / parent / base


def folder_cover_output(folder_rel: str) -> Path:
    key = folder_rel or 'root'
    name = slug(Path(key).name if key != 'root' else 'root') + '-' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:8] + '.jpg'
    return COVERS / '_folders' / name


def collect_pdfs() -> list[Path]:
    BOOKS.mkdir(exist_ok=True)
    pdfs = []
    for p in BOOKS.rglob('*'):
        if p.is_file() and p.suffix.lower() in PDF_EXTS and not is_hidden(p.relative_to(BOOKS)):
            pdfs.append(p)
    return sorted(pdfs, key=lambda x: x.relative_to(BOOKS).as_posix().lower())


def build_library(title: str) -> dict:
    DATA.mkdir(exist_ok=True)
    COVERS.mkdir(exist_ok=True)

    pdfs = collect_pdfs()
    books_by_folder: dict[str, list[dict]] = {}
    book_cover_files: dict[str, Path] = {}
    all_folders: set[str] = {''}

    for pdf in pdfs:
        rel = pdf.relative_to(BOOKS)
        folder_rel = rel.parent.as_posix() if rel.parent.as_posix() != '.' else ''
        parts = [] if folder_rel == '' else folder_rel.split('/')
        for i in range(1, len(parts) + 1):
            all_folders.add('/'.join(parts[:i]))
        all_folders.add(folder_rel)

        order, book_title = parse_book_title(pdf)
        cover_path = cover_output_for_pdf(pdf)
        make_pdf_cover(pdf, cover_path)
        cover_url = cover_path.relative_to(ROOT).as_posix()
        file_url = 'books/' + '/'.join(quote(part, safe='') for part in rel.parts)
        item = {
            'type': 'book',
            'title': book_title,
            'order': order,
            'file': file_url,
            'cover': cover_url,
            'folder': folder_rel,
            'path': rel.as_posix(),
        }
        books_by_folder.setdefault(folder_rel, []).append(item)
        book_cover_files[rel.as_posix()] = cover_path

    # Додаємо фізичні папки навіть без PDF, якщо там є icon.* або підпапки.
    if BOOKS.exists():
        for d in BOOKS.rglob('*'):
            if d.is_dir() and not is_hidden(d.relative_to(BOOKS)):
                rel = d.relative_to(BOOKS).as_posix()
                all_folders.add(rel)
                parts = rel.split('/') if rel else []
                for i in range(1, len(parts)):
                    all_folders.add('/'.join(parts[:i]))

    def descendant_cover_files(folder_rel: str) -> list[Path]:
        prefix = folder_rel + '/' if folder_rel else ''
        result = []
        for rel_str, cover_file in book_cover_files.items():
            if rel_str.startswith(prefix):
                result.append(cover_file)
        return result[:4]

    folder_meta: dict[str, dict] = {}
    for folder_rel in sorted(all_folders, key=lambda s: (s.count('/'), s.lower())):
        physical = BOOKS / folder_rel if folder_rel else BOOKS
        title_for_folder = Path(folder_rel).name if folder_rel else title
        icon = find_folder_icon(physical)
        if icon:
            icon_rel = icon.relative_to(BOOKS)
            cover_url = 'books/' + '/'.join(quote(part, safe='') for part in icon_rel.parts)
            cover_source = 'icon'
        else:
            collage = folder_cover_output(folder_rel)
            make_collage(title_for_folder, descendant_cover_files(folder_rel), collage)
            cover_url = collage.relative_to(ROOT).as_posix()
            cover_source = 'collage'
        folder_meta[folder_rel] = {
            'type': 'folder',
            'title': title_for_folder,
            'path': folder_rel,
            'cover': cover_url,
            'coverSource': cover_source,
            'items': [],
            'bookCount': 0,
        }

    # Вкладаємо папки одна в одну.
    for folder_rel in sorted(all_folders, key=lambda s: s.count('/')):
        if folder_rel == '':
            continue
        parent_rel = Path(folder_rel).parent.as_posix()
        if parent_rel == '.':
            parent_rel = ''
        folder_meta[parent_rel]['items'].append(folder_meta[folder_rel])

    # Додаємо книги у відповідні папки.
    for folder_rel, items in books_by_folder.items():
        folder_meta[folder_rel]['items'].extend(items)

    def sort_items(items: list[dict]) -> None:
        for it in items:
            if it.get('type') == 'folder':
                sort_items(it['items'])
        items.sort(key=lambda it: (
            0 if it.get('type') == 'folder' else 1,
            it.get('order') if it.get('order') is not None else 10**9,
            it.get('title', '').casefold(),
        ))

    def count_books(node: dict) -> int:
        total = 0
        for it in node['items']:
            if it.get('type') == 'book':
                total += 1
            elif it.get('type') == 'folder':
                total += count_books(it)
        node['bookCount'] = total
        return total

    root_node = folder_meta['']
    sort_items(root_node['items'])
    total = count_books(root_node)

    flat_books = []
    def walk(node: dict) -> None:
        for it in node['items']:
            if it.get('type') == 'book':
                flat_books.append(it)
            elif it.get('type') == 'folder':
                walk(it)
    walk(root_node)

    data = {
        'version': 2,
        'title': title,
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'supportsNestedFolders': True,
        'folderIconNames': list(ICON_NAMES),
        'totalBooks': total,
        'items': root_node['items'],
        'flatBooks': flat_books,
    }
    (DATA / 'library.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return data


def copy_to_dist(out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    for name in ['index.html', 'app.js', 'style.css', 'manifest.webmanifest', 'sw.js']:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, out / name)
    for folder in ['icons', 'books', 'data', 'covers']:
        src = ROOT / folder
        if src.exists():
            shutil.copytree(src, out / folder, dirs_exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='', help='Optional output folder, for example dist')
    parser.add_argument('--title', default='PDF Library')
    args = parser.parse_args()
    data = build_library(args.title)
    if args.out:
        copy_to_dist(ROOT / args.out)
        print(f'Built {args.out}/index.html')
    print(f'Books found: {data["totalBooks"]}')
    print('Nested folders: enabled')
    print('Folder icons: icon.png/icon.jpg/icon.jpeg, fallback collage if absent')


if __name__ == '__main__':
    main()
