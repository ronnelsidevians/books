#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import argparse, json, re, unicodedata
ROOT=Path(__file__).resolve().parent
BOOKS=ROOT/'books'; DATA=ROOT/'data'; COVERS=ROOT/'covers'
TR={'а':'a','б':'b','в':'v','г':'h','ґ':'g','д':'d','е':'e','є':'ie','ж':'zh','з':'z','и':'y','і':'i','ї':'i','й':'i','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ь':'','ю':'iu','я':'ia','ы':'y','э':'e','ъ':'','ё':'yo'}

def slug(s):
    s=''.join(TR.get(c,c) for c in s.lower())
    s=unicodedata.normalize('NFKD',s)
    s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+','-',s).strip('-') or 'book'

def parse_series_and_order(pdf):
    rel = pdf.relative_to(BOOKS)
    series = ''
    order = None
    title = pdf.stem.strip()
    if len(rel.parts) > 1:
        series = rel.parts[0]
        m = re.match(r'^\s*(\d+)[\s._\-–—]+(.+)$', title)
        if m:
            order = int(m.group(1))
            title = m.group(2).strip()
    return series, order, title

def render_cover(pdf_path,out,zoom=2.0):
    try:
        import fitz
        from PIL import Image
        doc=fitz.open(str(pdf_path)); page=doc.load_page(0); r=page.rect
        clip=fitz.Rect(r.x0+r.width/2,r.y0,r.x1,r.y1)  # права половина першої сторінки
        pix=page.get_pixmap(matrix=fitz.Matrix(zoom,zoom),clip=clip,alpha=False)
        img=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
        target=2/3; w,h=img.size
        if h and w/h>target:
            nw=int(h*target); left=max(0,(w-nw)//2); img=img.crop((left,0,left+nw,h))
        if img.width>720:
            nh=int(img.height*(720/img.width)); img=img.resize((720,nh),Image.LANCZOS)
        out.parent.mkdir(exist_ok=True); img.save(out,'JPEG',quality=88,optimize=True); return True
    except Exception as e:
        print('Cover skipped:', pdf_path.name, e); return False

def main():
    p=argparse.ArgumentParser(); p.add_argument('--title',default='Моя PDF-бібліотека'); p.add_argument('--author',default='Невідомий автор'); p.add_argument('--category',default='PDF'); p.add_argument('--cover-zoom',type=float,default=2.0); a=p.parse_args()
    BOOKS.mkdir(exist_ok=True); DATA.mkdir(exist_ok=True); COVERS.mkdir(exist_ok=True)
    pdfs=sorted([x for x in BOOKS.rglob('*') if x.is_file() and x.suffix.lower()=='.pdf'], key=lambda x:str(x.relative_to(BOOKS)).lower())
    used=set(); books=[]; covers=0
    for pdf in pdfs:
        series, order, title = parse_series_and_order(pdf)
        base=slug((series+'-' if series else '') + title); ident=base; i=2
        while ident in used: ident=f'{base}-{i}'; i+=1
        used.add(ident)
        cover_file=COVERS/f'{ident}.jpg'; ok=render_cover(pdf,cover_file,a.cover_zoom); covers += 1 if ok else 0
        rel='books/' + '/'.join(pdf.relative_to(BOOKS).parts)
        books.append({'id':ident,'title':title,'author':a.author,'category':a.category,'file':rel,'cover':'covers/'+cover_file.name if ok else '', 'series':series, 'order':order, 'tags':[]})
    books.sort(key=lambda b:(b.get('series') or 'яяя', b.get('order') if b.get('order') is not None else 999999, b['title'].lower()))
    (DATA/'books.json').write_text(json.dumps({'title':a.title,'books':books},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PDF found: {len(books)}')
    print(f'Covers generated: {covers}')
    print('Generated data/books.json')
if __name__=='__main__': main()
