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

def parse(pdf):
    rel=pdf.relative_to(BOOKS); title=pdf.stem.strip(); series=''; order=None
    if len(rel.parts)>1:
        series=rel.parts[0]
        m=re.match(r'^\s*(\d+)[\s._\-–—]+(.+)$', title)
        if m:
            order=int(m.group(1)); title=m.group(2).strip()
    return series,order,title

def fallback_cover(out,title):
    from PIL import Image, ImageDraw, ImageFont
    img=Image.new('RGB',(720,780),(250,204,21)); d=ImageDraw.Draw(img)
    d.rectangle([0,0,90,780], fill=(146,64,14))
    try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',48)
    except Exception: font=None
    d.multiline_text((130,250), title[:90], fill=(15,23,42), font=font, spacing=10)
    img.save(out,'JPEG',quality=88)

def cover(pdf,out,zoom=2.0):
    """Cover = right half of first page, top anchored, cropped vertically to hide lower text band."""
    try:
        import fitz
        from PIL import Image
        doc=fitz.open(str(pdf)); page=doc.load_page(0); r=page.rect
        clip=fitz.Rect(r.x0+r.width/2,r.y0,r.x1,r.y1)
        pix=page.get_pixmap(matrix=fitz.Matrix(zoom,zoom),clip=clip,alpha=False)
        img=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
        # top crop: keep upper 78%, so bottom title/text band does not appear in cards
        w,h=img.size
        img=img.crop((0,0,w,int(h*0.78)))
        # force a wider/shorter cover ratio; card CSS will object-position: top
        target=0.82
        w,h=img.size
        if h and w/h < target:
            nh=int(w/target)
            img=img.crop((0,0,w,min(h,nh)))
        if img.width>760:
            nh=int(img.height*(760/img.width)); img=img.resize((760,nh),Image.LANCZOS)
        out.parent.mkdir(exist_ok=True); img.save(out,'JPEG',quality=88,optimize=True); return True
    except Exception as e:
        print('Cover fallback:', pdf.name, e); fallback_cover(out,pdf.stem); return True

def make_collage(series_name, cover_paths, out):
    from PIL import Image, ImageDraw, ImageFont
    W,H=720,780
    img=Image.new('RGB',(W,H),(245,239,222)); d=ImageDraw.Draw(img)
    d.rectangle([0,0,W,H], outline=(20,20,20), width=10)
    slots=[(36,42,342,340),(378,42,684,340),(36,370,342,668),(378,370,684,668)]
    for i,slot in enumerate(slots):
        if i<len(cover_paths) and Path(cover_paths[i]).exists():
            c=Image.open(cover_paths[i]).convert('RGB'); c.thumbnail((slot[2]-slot[0],slot[3]-slot[1]))
            x=slot[0]+((slot[2]-slot[0])-c.width)//2; y=slot[1]
            img.paste(c,(x,y)); d.rectangle(slot, outline=(20,20,20), width=4)
        else:
            d.rectangle(slot, fill=(230,220,200), outline=(20,20,20), width=4)
    d.rectangle([0,H-82,W,H], fill=(20,20,20))
    try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',34)
    except Exception: font=None
    d.text((30,H-60), series_name[:32], fill=(245,239,222), font=font)
    out.parent.mkdir(exist_ok=True); img.save(out,'JPEG',quality=88,optimize=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--title',default='Моя PDF-бібліотека')
    p.add_argument('--author',default='Oleksandr Ryzhkov')
    p.add_argument('--category',default='PDF')
    p.add_argument('--cover-zoom',type=float,default=2.0)
    a=p.parse_args()
    BOOKS.mkdir(exist_ok=True); DATA.mkdir(exist_ok=True); COVERS.mkdir(exist_ok=True)
    pdfs=sorted([x for x in BOOKS.rglob('*') if x.is_file() and x.suffix.lower()=='.pdf'], key=lambda x:str(x.relative_to(BOOKS)).lower())
    used=set(); books=[]; by_series={}
    for pdf in pdfs:
        series,order,title=parse(pdf)
        base=slug((series+'-' if series else '')+title); ident=base; i=2
        while ident in used: ident=f'{base}-{i}'; i+=1
        used.add(ident)
        cf=COVERS/f'{ident}.jpg'; cover(pdf,cf,a.cover_zoom)
        rel='books/'+'/'.join(pdf.relative_to(BOOKS).parts)
        item={'id':ident,'title':title,'author':a.author,'category':a.category,'file':rel,'cover':'covers/'+cf.name,'series':series,'order':order,'tags':[]}
        books.append(item)
        if series: by_series.setdefault(series,[]).append(item)
    books.sort(key=lambda b:(b.get('series') or 'яяя', b.get('order') if b.get('order') is not None else 999999, b['title'].lower()))
    series_list=[]
    for s,arr in sorted(by_series.items(), key=lambda kv:kv[0].lower()):
        arr=sorted(arr,key=lambda b:(b.get('order') if b.get('order') is not None else 999999,b['title'].lower()))
        collage=COVERS/(slug(s)+'-series.jpg')
        make_collage(s,[ROOT/b['cover'] for b in arr[:4]],collage)
        series_list.append({'id':slug(s),'title':s,'cover':'covers/'+collage.name,'count':len(arr),'bookIds':[b['id'] for b in arr]})
    (DATA/'books.json').write_text(json.dumps({'title':a.title,'books':books,'series':series_list},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PDF found: {len(books)}')
    print(f'Series found: {len(series_list)}')
    print('Generated data/books.json')
if __name__=='__main__': main()
