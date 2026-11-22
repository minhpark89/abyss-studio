import requests,concurrent.futures
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
b=Path(__file__).resolve().parent
def query(name,title):
    url='https://commons.wikimedia.org/w/api.php'
    q=dict(action='query',titles='File:'+title,prop='revisions|imageinfo',rvprop='content',rvslots='main',iiprop='url',iiurlwidth=1280,format='json')
    r=requests.get(url,params=q,headers={'User-Agent':'AbyssFieldnotesEditorial/1.0'},timeout=20)
    row=next(iter(r.json()['query']['pages'].values()))
    print(name,row['revisions'][0]['slots']['main']['*'][:2000],flush=True)
    v=row['imageinfo'][0];suffix='.ogv' if name=='swimmers' else '.jpg'
    for target in [v.get('thumburl'),v['url']]:
        if not target:continue
        r=requests.get(target,headers={'User-Agent':'AbyssFieldnotesEditorial/1.0'},timeout=18);print(name,r.status_code,len(r.content),flush=True)
        if r.ok and len(r.content)>5000 and 'html' not in r.headers.get('content-type',''):
            (b/'media'/(name+suffix)).write_bytes(r.content);break
jobs={'fish':'Lanternfish by NOAA.jpg','rov':'Deep Discoverer on NOAA Ship Okeanos Explorer.jpg','swimmers':'Multi-jet-propulsion-organized-by-clonal-development-in-a-colonial-siphonophore-ncomms9158-s2.ogv'}
with concurrent.futures.ThreadPoolExecutor() as ex:
    fs=[ex.submit(query,n,t) for n,t in jobs.items()]
    for f in fs:
        try:f.result()
        except Exception as e:print(e)

