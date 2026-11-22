from pathlib import Path
import requests, json
from bs4 import BeautifulSoup
from PIL import Image
base=Path(__file__).resolve().parent
media=base/'media'
media.mkdir(exist_ok=True)
s=requests.Session()
s.headers['User-Agent']='AbyssFieldnotes/1.0 (documentary image research)'
title='File:Physonect siphonophore Puerto Rico April 2015.png'
api=s.get('https://commons.wikimedia.org/w/api.php',params=dict(action='query',titles=title,prop='imageinfo',iiprop='url|extmetadata',format='json'),timeout=20)
row=next(iter(api.json()['query']['pages'].values()))['imageinfo'][0]
def clean(item):
    return BeautifulSoup(item['value'],'html.parser').get_text(' ',strip=True)
metadata={k:clean(v) for k,v in row['extmetadata'].items() if k in ('ImageDescription','Artist','LicenseShortName','Credit','DateTimeOriginal')}
file=media/'field.png'
r=s.get(row['url'].split('?')[0],timeout=30)
r.raise_for_status()
file.write_bytes(r.content)
im=Image.open(file)
im.thumbnail((600,450))
im.convert('RGB').save(media/'field-inspection.jpg')
metadata.update(source=row['descriptionurl'],original=row['url'].split('?')[0],credit_html=row['extmetadata']['Credit']['value'])
(media/'field-source.json').write_text(json.dumps(metadata,indent=2),'utf8')
print(metadata)

