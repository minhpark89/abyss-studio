from pathlib import Path
import requests,re,json,concurrent.futures
from bs4 import BeautifulSoup
b=Path(__file__).resolve().parent
def fetch(name):
    key,index,suffix={'fish':('fish',0,'.jpg'),'rov':('rov',1,'.jpg'),'swimmers':('nanomia',0,'.ogv'),'steer':('nanomia',1,'.ogv')}[name]
    row=json.loads((b/'research'/(key+'-options.json')).read_text())[index]
    src=row['url']
    urls=[src]
    if suffix=='.jpg':
        urls.insert(0,src.replace('/commons/','/commons/thumb/')+'/960px-'+src.split('/')[-1])
    if name in ['swimmers','steer']:
        urls.append('https://static-content.springer-cdn.net/esm/art%3A10.1038%2Fncomms9158/MediaObjects/41467_2015_BFncomms9158_MOESM'+str(index+2)+'_ESM.mov')
    for url in urls:
        try:
            r=requests.get(url,timeout=18);ct=r.headers.get('Content-Type','');print(name,r.status_code,ct,flush=True)
            if r.ok and len(r.content)>2000 and 'html' not in ct:
                (b/'media'/(name+suffix)).write_bytes(r.content);return
        except requests.RequestException as e:print(name,type(e).__name__)
    if name=='fish':
        page=BeautifulSoup(requests.get(row['source'],timeout=15).content,'html.parser')
        print('NOAA URLS',[(a.get_text(' ',strip=True)[:60],a.get('href')) for a in page.select('a[href]') if 'noaa.gov' in a.get('href','') or 'flickr.com' in a.get('href','')][:10])
with concurrent.futures.ThreadPoolExecutor() as ex:list(ex.map(fetch,['fish','rov','swimmers','steer']))

