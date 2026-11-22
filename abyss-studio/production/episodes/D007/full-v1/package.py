from pathlib import Path
import json,math,textwrap,html
from PIL import Image, ImageDraw, ImageFont,ImageOps,ImageEnhance
b=Path(__file__).resolve().parent;d=b/'delivery'
def read(p):return json.loads((b/p).read_text('utf8'))
def put(name,v):(d/name).write_text(v+'\n','utf8')
def stamp(s):return f'{int(s)//60}:{int(s)%60:02d}'
times=read('qa/chapters.json')
chapters=[(0,'One hunter or a colony?'),(times['trace'],'Following the shared stem'),(times['turn'],'Which swimming bell steers?'),(times['dark'],'A red lure in the dark'),(times['vehicle'],'Following a colony with an ROV'),(times['return'],'Reading the photograph again')]
chap='\n'.join(f'{stamp(t)} {name}' for t,name in chapters)
title='This Deep-Sea Hunter Is a Colony'
photos=[dict(asset='Puerto Rico physonect field photograph',credit='NOAA Office of Ocean Exploration and Research',license='Public domain',source=read('../opening-v1/media/field-source.json')['source']),
dict(asset='Nanomia bijuga, frame from supplementary Movie 1 and Figure 1',credit='Costello, Colin, Gemmell, Dabiri and Sutherland (2015); Figure 1 modified from their ref. 12',license='CC BY 4.0',license_url='https://creativecommons.org/licenses/by/4.0/',source='https://www.nature.com/articles/ncomms9158',presentation='Film still and diagram placed side by side'),
dict(asset='Spotted lanternfish specimen',credit='Julien Savoie',license='CC BY 4.0',license_url='https://creativecommons.org/licenses/by/4.0/',source='https://www.gbif.org/occurrence/6235768722',presentation='Full photograph resized and caption added'),
dict(asset='Deep Discoverer on deployment, NOAA OER',credit='NOAA Ocean Exploration, Gulf of Mexico 2017',license='Public domain',source='https://oceanexplorer.noaa.gov/multimedia/okeanos-explorations-ex1711-dailyupdates-media-video-d2-d2/',presentation='Frame from expedition film')]
rights=dict(photos=photos,science=read('facts.json')['claims'],opening=read('../opening-v1/delivery/credits.json'),motion=read('web/plates.json'),models='Original illustrative geometry, scale and light are schematic',audio='Original score and Kokoro-82M am_michael US English narration')
put('rights-and-sources.json',json.dumps(rights,indent=2))
put('title-en.txt',title);put('chapters.txt',chap)
description="Watch a siphonophore turn, and the youngest swimming bells have a surprisingly important job. Follow the same stem toward the tentacles and the job changes again. In the deep Pacific, one species carries a twitching red lure.\n\n"+chap+"\n\nField images and research\n"+'\n'.join(f"{p['asset']} — {p['credit']} ({p['license']}). {p['source']}" for p in photos)+"\nCC BY 4.0: https://creativecommons.org/licenses/by/4.0/\n\n"+'\n'.join(dict.fromkeys(v[2] for v in rights['science']))+"\n\nReconstructed scenes are labeled on screen. Anatomy and water flow are illustrated."
put('description-en.txt',description)
fonts=Path('C:/Windows/Fonts')
def thumb(name,source,words,sub):
    im=Image.open(b/'qa/source-frames'/source).convert('RGB').resize((1280,720))
    if name=='B':im=ImageOps.mirror(im)
    im=ImageEnhance.Contrast(im).enhance(1.14)
    layer=Image.new('RGBA',im.size);g=ImageDraw.Draw(layer)
    for x in range(1280):
        alpha=int(234*max(0,min(1,(x-370)/520)))
        g.line((x,0,x,720),fill=(2,12,21,alpha))
    im=Image.alpha_composite(im.convert('RGBA'),layer);g=ImageDraw.Draw(im)
    def f(n):return ImageFont.truetype(str(fonts/'segoeuib.ttf'),n)
    x=676;y=178
    g.rectangle((x,146,x+77,154),fill='#efb438')
    for i,line in enumerate(words):
        g.text((x,y+i*119),line,font=f(101),fill='#f5bc41' if i==1 else '#f3eee4',stroke_width=2,stroke_fill='#132330')
    im.convert('RGB').save(d/f'thumbnail-{name}.jpg',quality=94)
thumb('A','swim-045.jpg',['ONE','ANIMAL?'],'');thumb('B','curtain-035.jpg',['WHO','HUNTS?'],'')
buttons=''.join(f'<button data-time="{t:.3f}">{stamp(t)} &nbsp;{html.escape(n)}</button>' for t,n in chapters)
page=(b.parent/'opening-v1/delivery/review.html').read_text('utf8').replace('D007-opening.mp4','D007.mp4').replace('opening-poster.jpg','thumbnail-A.jpg').replace('Opening review','Full episode review').replace('· Opening','· Full episode').replace('Download the opening','Download the episode').replace('credits.json','rights-and-sources.json')
a=page.index('<nav>');z=page.index('</nav>')
page=page[:a]+'<nav>'+buttons+page[z:]
put('review.html',page)
put('YOUTUBE_UPLOAD.md','# Abyss Fieldnotes · D007\n\nReview D007.mp4 and its English captions. Use title-en.txt and description-en.txt, choose a thumbnail and attach D007-en-US.srt. The film contains labeled realistic AI reconstructions. Select the appropriate altered-content disclosure in YouTube Studio. The owner controls approval and publication.')
put('metadata.json',json.dumps(dict(episode='D007',title=title,language='en-US',market='US',release_status='awaiting_owner_review',youtube_published=False,thumbnail='thumbnail-A.jpg'),indent=2))

