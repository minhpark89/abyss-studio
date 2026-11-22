"""Read/validate persistent production state. Never generates or publishes."""
import argparse, hashlib, json, sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent

def validate(root, state_override=None):
    prod=root/'production'
    state=state_override if state_override is not None else json.loads((prod/'state.json').read_text(encoding='utf-8'))
    plan=json.loads((prod/'content-plan.json').read_text(encoding='utf-8'))
    sources={s['id'] for s in json.loads((prod/'sources.json').read_text(encoding='utf-8'))['sources']}
    issues=[]
    ids=[e['id'] for e in state['episodes']]
    if len(ids)!=len(set(ids)): issues.append('Duplicate episode IDs')
    if set(ids)!={e['id'] for e in plan['episodes']}: issues.append('Plan/state episode mismatch')
    if state['active_episode'] not in ids: issues.append('Active episode missing')
    if state['format']!=plan['format']: issues.append('Format mismatch')
    for p in plan['episodes']:
        if not set(p['source_ids']).issubset(sources): issues.append(p['id']+': unknown source ID')
        if not p['question_text'] or len(p['beats'])<3: issues.append(p['id']+': incomplete story')
    job_markers=set()
    for ep in state['episodes']:
        folder=prod/'episodes'/ep['id']
        if not (folder/'BRIEF.md').is_file(): issues.append(ep['id']+': missing brief')
        unfinished=False
        next_stage=None
        for stage in state['checkpoints']:
            c=ep['checks'].get(stage,{})
            status=c.get('status')
            if status not in ('pending','in_progress','passed','needs_revision'): issues.append(ep['id']+': invalid checkpoint '+stage)
            if status!='passed': unfinished=True; next_stage=next_stage or stage
            elif unfinished: issues.append(ep['id']+': passed checkpoint after unfinished prerequisite '+stage)
            if status=='passed' and not c.get('evidence'): issues.append(ep['id']+': passed without evidence '+stage)
            for evidence in c.get('evidence',[]):
                path=(root/evidence['path']).resolve()
                if not path.is_relative_to(root.resolve()): issues.append(ep['id']+': evidence outside workspace');continue
                if not path.is_file(): issues.append(ep['id']+': evidence missing '+evidence['path']);continue
                if hashlib.sha256(path.read_bytes()).hexdigest()!=evidence.get('sha256'): issues.append(ep['id']+': stale evidence '+evidence['path'])
        if next_stage and ep['stage']!=next_stage: issues.append(ep['id']+': current stage does not match earliest unfinished checkpoint')
        if ep['status']=='ready_for_user_review' and next_stage: issues.append(ep['id']+': ready without all production checkpoints')
        for j in ep.get('active_jobs',[]):
            key=j.get('marker')
            if not key or key in job_markers: issues.append(ep['id']+': missing/duplicate job marker')
            job_markers.add(key)
            if j.get('submitted_at') and not j.get('thread_url') and j.get('status')!='needs_attention': issues.append(ep['id']+': ambiguous submission must need attention')
        if ep['publication']['status']=='published' and (not ep['publication'].get('url') or not ep['publication'].get('published_at')): issues.append(ep['id']+': published without URL/time')
    if state['automation']['status']=='active' and not state['automation'].get('task_id'): issues.append('Automation active without real task ID')
    return state,issues

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--validate',action='store_true');args=parser.parse_args()
    state,issues=validate(ROOT)
    active=next(e for e in state['episodes'] if e['id']==state['active_episode'])
    result={'valid':not issues,'issues':issues,'episode_count':len(state['episodes']),'active_episode':active['id'],'title':active['title'],'checkpoint':active['stage'],'automation':state['automation']['status'],'ready_for_review':sum(e['status']=='ready_for_user_review' for e in state['episodes'])}
    if active.get('active_build'):result['active_build']=active['active_build']
    if active.get('hook_preview'):
        result['active_hook_preview']={k:active['hook_preview'].get(k) for k in ['version','status','file','duration_s','caption_kind','human_listening','owner_acceptance']}
    if active.get('active_jobs'):result['active_jobs']=active['active_jobs']
    result['local_review_edits_available']=sum(e.get('review_edit',{}).get('status')=='available_for_joint_review' for e in state['episodes'])
    result['active_review_edit']={k:active.get('review_edit',{}).get(k) for k in ['status','file','duration_s','not_release_cleared']}
    proof=active.get('visual_revision_proof') or active.get('revision_proof')
    if proof:
        result['active_visual_revision_proof']={k:proof.get(k) for k in ['status','file','duration_s','owner_style_acceptance','scope']}
    if active.get('hybrid_form_trial'):
        result['active_hybrid_form_trial']={k:active['hybrid_form_trial'].get(k) for k in ['status','file','duration_s','scope','technical_qc','human_listening','owner_style_acceptance','next_action']}
    connection=ROOT/state['muse']['connection_file']
    if connection.exists():
        c=json.loads(connection.read_text(encoding='utf-8'));result['muse']={k:c.get(k) for k in ['status','checkedAt','quota','capacityMeasured']}
        result['muse']['video_generation']=state['muse'].get('video_generation',{})
        if state['muse'].get('account_review'):
            result['muse']['account_review']={k:state['muse']['account_review'].get(k) for k in ['status','account_email_verified','generation_retested']}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(1 if issues else 0)
