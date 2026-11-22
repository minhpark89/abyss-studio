import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {root} from './config.js';

const cache = new Map();
const relative = file => path.relative(root, file).replaceAll('\\', '/');
export function readProductionJSON(file, fallback = null) {
  try {
    const stat = fs.statSync(file), key = `${stat.mtimeMs}:${stat.size}`;
    if (cache.get(file)?.key === key) return cache.get(file).value;
    const value = JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
    cache.set(file, {key, value});
    return value;
  } catch (error) {
    if (error.code === 'ENOENT') return fallback;
    throw error;
  }
}
const dirs = base => fs.existsSync(base) ? fs.readdirSync(base, {withFileTypes:true}).filter(e => e.isDirectory()).map(e => e.name) : [];
const exists = file => typeof file === 'string' && fs.existsSync(path.join(root, file));
export function jobCategory(receipt) {
  if (receipt.clip?.path) return receipt.visual_qa === 'rejected' ? 'rejected' : receipt.visual_qa === 'passed' ? 'approved' : 'review';
  if (receipt.status === 'provider_terminal') return 'terminal';
  if (receipt.attempted_at && !receipt.clip?.path) return 'attention';
  return 'prepared';
}
export class ProductionIndex {
  constructor(base = root) { this.root = base; this.cached = null; this.checked = 0; this.scans = 0; }
  snapshot(force = false) {
    if (!force && this.cached && Date.now() - this.checked < 1000) return this.cached;
    const start = performance.now();
    const relative = file => path.relative(this.root,file).replaceAll('\\','/');
    const state = readProductionJSON(path.join(this.root, 'production/state.json'), {});
    const attempts = [], usage = {}, warnings = [];
    for (const ep of state.episodes || []) {
      const episodeRoot = path.join(this.root, 'production/episodes', ep.id);
      for (const revision of dirs(episodeRoot).filter(x => /^revision-v\d+$/.test(x))) {
        const revisionRoot = path.join(episodeRoot, revision);
        for (const attempt of dirs(revisionRoot).filter(x => /^muse-native-v\d+(?:-|$)/.test(x))) {
          const base = path.join(revisionRoot, attempt), file = path.join(base, 'manifest.json');
          try {
            const manifest = readProductionJSON(file);
            if (!manifest?.jobs) continue;
            for (const name of fs.readdirSync(base).filter(n => /^usage-(before|after)-.*\.json$/.test(n))) {
              const u = readProductionJSON(path.join(base, name));
              if (u?.quota?.verified && (!usage[manifest.profile_key] || u.checked_at > usage[manifest.profile_key].checked_at)) usage[manifest.profile_key] = {checked_at:u.checked_at, quota:u.quota};
            }
            for (const job of manifest.jobs) {
              const receiptPath = path.join(base, 'receipts', job.id + '.json');
              const r = readProductionJSON(receiptPath, {});
              const id = createHash('sha256').update(relative(file) + ':' + job.id).digest('hex').slice(0, 24);
              attempts.push({id, episode:manifest.episode, version:manifest.version, target_revision:manifest.target_revision || revision, attempt_version:manifest.attempt_version,
                scene:job.id, profile_key:job.profile_key || manifest.profile_key, status:r.status || 'missing_receipt', category:jobCategory(r), thread_url:r.thread_url,
                clip:r.clip?.path, clip_sha256:r.clip?.sha256, clip_exists:typeof r.clip?.path==='string'&&fs.existsSync(path.join(this.root,r.clip.path)), visual_qa:r.visual_qa || 'pending', duration:r.clip?.duration_s,
                created_at:r.created_at || manifest.created_at, attempted_at:r.attempted_at, submitted_at:r.submitted_at, completed_at:r.downloaded_at || r.completed_at,
                updated_at:r.checked_at || r.downloaded_at || r.submitted_at || r.attempted_at || r.created_at,
                manifest:relative(file), receipt:relative(receiptPath), marker:job.marker});
            }
          } catch(error) { warnings.push({path:relative(file), error:error.message}); }
        }
      }
    }
    const episodes = (state.episodes || []).map(ep => ({id:ep.id, title:ep.title, status:ep.status, checkpoint:ep.stage||ep.current_checkpoint||ep.checkpoint,
      publication:ep.publication, build:ep.active_build, review:ep.review_edit, gates:ep.checks||ep.checkpoints||ep.gates,
      jobs:attempts.filter(j => j.episode === ep.id).length}));
    const active = episodes.find(ep => ep.id === state.active_episode) || episodes[0] || {};
    const counts = Object.fromEntries(['prepared','attention','terminal','review','approved','rejected'].map(k => [k, attempts.filter(j => j.category === k).length]));
    this.scans++;
    this.cached = {active_episode:state.active_episode, episodes, attempts, usage, warnings, automation:state.automation, counts,
      episode:{...active, duration:active.review?.duration_s || active.build?.duration_s || active.build?.duration_seconds},
      index:{scan_ms:performance.now()-start, scans:this.scans, scanned_at:new Date().toISOString()}};
    this.checked = Date.now();
    return this.cached;
  }
  detail(id) {
    const job = this.snapshot().attempts.find(j => j.id === id);
    if (!job) return null;
    const manifest = readProductionJSON(path.join(this.root, job.manifest));
    const item = manifest.jobs.find(j => j.id === job.scene);
    const r = readProductionJSON(path.join(this.root, job.receipt), {});
    return {...job, prompt:item.prompt, reference:item.reference, reason:r.reason || r.error || r.visual_qa_notes || r.review_notes || null,
      receipt_data:Object.fromEntries(['episode','version','scene_id','job_key','marker','prompt_sha256','profile_key','status','created_at','attempted_at','submitted_at','downloaded_at','checked_at','thread_url','clip','visual_qa','reason'].filter(k => r[k] !== undefined).map(k => [k,r[k]]))};
  }
  upload(episode) {
    const ep = this.snapshot().episodes.find(x => x.id === episode);
    const pack = ep?.build?.upload_package;
    if (!pack) return null;
    const location = path.resolve(this.root, typeof pack === 'string' ? pack : pack.path);
    const episodeDir = path.resolve(this.root, 'production/episodes', episode);
    if (!location.startsWith(episodeDir + path.sep) || !fs.existsSync(location)) return null;
    const base = fs.statSync(location).isDirectory() ? location : path.dirname(location);
    const file = path.join(base, 'YOUTUBE_UPLOAD.md');
    const descriptionFile=path.join(base,'description-en.txt');
    const packageMeta=readProductionJSON(path.join(base,'metadata.json'),{});
    const titleFile = ['title-en.txt','title.txt'].map(name => path.join(base,name)).find(f => fs.existsSync(f));
    const thumbnails = (ep.build.thumbnails || []).map(t => typeof t === 'string' ? {path:t} : t);
    return {episode, title:titleFile ? fs.readFileSync(titleFile,'utf8').trim() : packageMeta.title || ep.title,
      description:fs.existsSync(descriptionFile)?fs.readFileSync(descriptionFile,'utf8').trim():null, text:fs.existsSync(file) ? fs.readFileSync(file,'utf8') : '',
      thumbnails, review:ep.review, status:ep.publication};
  }
}
export const productionIndex = new ProductionIndex();
