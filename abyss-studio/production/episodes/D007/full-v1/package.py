from pathlib import Path
import json,html
from PIL import Image
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
rights['thumbnails'] = {'method': 'Original AI-generated documentary illustrations', 'generator': 'OpenAI ImageGen', 'A': 'Erenna lure and lanternfish', 'B': 'Colony of swimming bells'}
put('rights-and-sources.json',json.dumps(rights,indent=2))
put('title-en.txt',title);put('chapters.txt',chap)
description="Watch a siphonophore turn, and the youngest swimming bells have a surprisingly important job. Follow the same stem toward the tentacles and the job changes again. In the deep Pacific, one species carries a twitching red lure.\n\n"+chap+"\n\nField images and research\n"+'\n'.join(f"{p['asset']} — {p['credit']} ({p['license']}). {p['source']}" for p in photos)+"\nCC BY 4.0: https://creativecommons.org/licenses/by/4.0/\n\n"+'\n'.join(dict.fromkeys(v[2] for v in rights['science']))+"\n\nReconstructed scenes are labeled on screen. Anatomy and water flow are illustrated."
put('description-en.txt',description)
for variant in ('A', 'B'):
    with Image.open(b/'thumbnail-ai'/f'original-{variant}.png') as source:
        source.convert('RGB').resize((1280, 720), Image.Resampling.LANCZOS).save(
            d/f'thumbnail-{variant}.jpg', quality=94, optimize=True)
buttons=''.join(f'<button data-time="{t:.3f}">{stamp(t)} &nbsp;{html.escape(n)}</button>' for t,n in chapters)
page=(b.parent/'opening-v1/delivery/review.html').read_text('utf8').replace('D007-opening.mp4','D007.mp4').replace('opening-poster.jpg','thumbnail-A.jpg').replace('Opening review','Full episode review').replace('· Opening','· Full episode').replace('Download the opening','Download the episode').replace('credits.json','rights-and-sources.json')
a=page.index('<nav>');z=page.index('</nav>')
page=page.replace('href="D007-en-US.srt" download>English captions','href="accessibility-upload/D007-en-US.srt" download="Fieldnotes-transcript.en-US.srt">Optional English caption file')
page=page[:a]+'<nav>'+buttons+page[z:]
posting_files = [
    ('title-en.txt', 'YouTube title'),
    ('description-en.txt', 'Full description and chapters'),
    ('thumbnail-A.jpg', 'Thumbnail A · WHY RED?'),
    ('thumbnail-B.jpg', "Thumbnail B · WHO'S STEERING?"),
]
posting_links = ' '.join(f'<a href="{file}" download>{label}</a>' for file,label in posting_files)
page = page.replace('</footer>', '</footer><section><h2>YouTube upload files</h2><nav aria-label="YouTube upload files">' + posting_links + '</nav></section>')
put('review.html',page)
put('YOUTUBE_UPLOAD.md','# Abyss Fieldnotes · D007\n\nOpen D007.mp4 for the version with captions already visible on screen. The optional English caption file for upload is in accessibility-upload/D007-en-US.srt. Keep that folder separate when copying the package for local playback. Use title-en.txt and description-en.txt, and choose thumbnail-A.jpg or thumbnail-B.jpg. Both thumbnail illustrations were generated with AI. The film contains labeled realistic AI reconstructions. The owner controls approval and publication.')
put('metadata.json',json.dumps(dict(episode='D007',title=title,language='en-US',market='US',release_status='awaiting_owner_review',youtube_published=False,thumbnail='thumbnail-A.jpg'),indent=2))

