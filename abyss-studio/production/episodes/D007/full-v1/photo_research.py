from pathlib import Path
import requests,json,concurrent.futures
from bs4 import BeautifulSoup
b=Path(__file__).resolve().parent
def query(job):
    key,search=job
    p={'action':'query','generator':'search','gsrsearch':search,'gsrnamespace':6,'gsrlimit':6,'prop':'imageinfo','iiprop':'url|extmetadata','format':'json'}
    r=requests.get('https://commons.wikimedia.org/w/api.php',params=p,headers={'User-Agent':'AbyssFieldnotes/1.0'},timeout=18)
    pages=r.json()['query']['pages'].values()
    data=[]
    for page in pages:
        v=page['imageinfo'][0];m=v['extmetadata']
        row={k:BeautifulSoup(m[k]['value'],'html.parser').get_text(' ',strip=True) for k in ['ImageDescription','Artist','LicenseShortName','LicenseUrl','Credit'] if k in m}
        row.update(title=page['title'],url=v['url'].split('?')[0],source=v['descriptionurl'])
        data.append(row)
    (b/'research'/(key+'-options.json')).write_text(json.dumps(data,indent=2),'utf8');print(key,[(d['title'],d['LicenseShortName']) for d in data],flush=True)
def figure():
    u='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4569723/fullTextXML'
    r=requests.get(u,timeout=25);s=BeautifulSoup(r.content,'xml')
    print('FIG',[(f.get('id'),f.caption.get_text(' ',strip=True)[:500],f.graphic.attrs if f.graphic else None) for f in s.select('fig')][:3],s.select_one('license'),flush=True)
    (b/'research/jets-figures.xml').write_bytes(r.content)
with concurrent.futures.ThreadPoolExecutor() as pool:
    fs=[pool.submit(query,job) for job in [('fish','lanternfish NOAA fish Myctophidae'),('rov','Deep Discoverer remotely operated vehicle NOAA on deck'),('nanomia','Nanomia bijuga Costello')]]+[pool.submit(figure)]
    for f in fs:
        try:f.result()
        except Exception as e:print(str(e))

