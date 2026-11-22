from pathlib import Path
import json,hashlib,datetime
b=Path(__file__).resolve().parent
prod=b.parents[2]
s=prod/'state.json'
state=json.loads(s.read_text('utf8'))
ep=next(e for e in state['episodes'] if e['id']=='D007')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
for key,files in [('C1_facts',['facts.json','research/jets.json','research/lure.json','research/growth.json','research/waves.json','research/mbari.json']),('C2_script',['story.json','../opening-v1/story.json']),('C3_storyboard',['storyboard.json','asset-manifest.json'])]:
    ep['checks'][key].update(status='passed',reviewed_at=now,evidence=[dict(path=(b/f).resolve().relative_to(prod.parent).as_posix(),sha256=hashlib.sha256((b/f).read_bytes()).hexdigest()) for f in files])
ep.update(stage='C4_preflight',status='full_in_production')
ep['hook_preview']['owner_acceptance']='accepted_opening'
ep['active_build'].update(version='full-v1',scope='full_episode_in_production',owner_acceptance='pending_full',opening_acceptance='accepted_opening',status='full_in_production')
ep['full_production']={'version':'full-v1','status':'in_progress','owner_authorized':True,'folder':b.relative_to(prod.parent).as_posix()}
state['updated_at']=now
tmp=s.with_suffix('.d007.tmp');tmp.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n','utf8');tmp.replace(s)

