from pathlib import Path
import requests,json,concurrent.futures
from bs4 import BeautifulSoup
base=Path(__file__).resolve().parent
out=base/'research'
out.mkdir(exist_ok=True)
def source(item):
    key,query=item
    if key=='mbari':
        r=requests.get(query,timeout=24);r.raise_for_status()
        s=BeautifulSoup(r.content,'html.parser').select_one('main')
        body={'url':query,'text':s.get_text(' ',strip=True),'figures':[n.get('data-elementor-lightbox-description') for n in s.select('[data-elementor-lightbox-description]')]}
    else:
        u='https://www.ebi.ac.uk/europepmc/webservices/rest/search'
        r=requests.get(u,params={'query':query,'resultType':'core','format':'json','pageSize':3},timeout=30);r.raise_for_status()
        body=[{k:row.get(k) for k in ['title','doi','pmcid','abstractText','authorString']} for row in r.json()['resultList']['result']]
    (out/(key+'.json')).write_text(json.dumps(body,indent=2),'utf8')
    print(key,str(body)[:2100],flush=True)
with concurrent.futures.ThreadPoolExecutor() as pool:
    list(pool.map(source,{'mbari':'https://www.mbari.org/animal/angler-siphonophore/','jets':'DOI:10.1038/ncomms9158','waves':'DOI:10.1242/jeb.245955','lure':'DOI:10.1126/science.1110441','growth':'TITLE_ABS:(siphonophore AND budding AND growth zones)'}.items()))

