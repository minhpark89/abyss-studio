import fs from 'node:fs';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {data, root} from './config.js';
import {readProductionJSON} from './production-index.js';
import {channelBoard} from './channel-board.js';

const run = promisify(execFile);
const feedFile = path.join(data, 'fieldnotes-feed.json');
const logFile = process.env.ABYSS_FIELDNOTES_METRICS || path.join(data, 'fieldnotes-metrics.json');
const loadState = () => readProductionJSON(path.join(root, 'production/state.json'));
const loadMetrics = () => readProductionJSON(logFile, []);
const checkpointFile = path.join(root,'production/channels/abyss-fieldnotes/checkpoint.json');
let pending, lastAttempt = 0, feedError = '';

export function updateFeed(force = false) {
  const cache = readProductionJSON(feedFile, {});
  const age = Date.now() - Date.parse(cache.checked_at);
  if (pending) return pending;
  if (Date.now() - lastAttempt < 60_000 || (!force && age < 900_000)) return;
  lastAttempt = Date.now();
  pending = run('python', ['-X','utf8',path.join(root,'scripts/fieldnotes-feed.py')],
    {windowsHide:true, timeout:15_000})
    .then(() => {feedError = '';}, () => {feedError = 'Chưa kết nối được feed YouTube. Bảng đang hiển thị lần đọc gần nhất.';})
    .finally(() => {pending = null;});
  return pending;
}

function publicVideo(ep, videos) {
  const known = ep.publication?.video_id;
  if (known) return videos[known] ? [known,videos[known]] : [];
  const matches = Object.entries(videos).filter(([,v]) => v.title === ep.title);
  return matches.length === 1 ? matches[0] : [];
}
export function fieldnotes() {
  const state = loadState();
  const checkpoint = readProductionJSON(checkpointFile);
  const feed = readProductionJSON(feedFile, {videos:{}});
  const historical = readProductionJSON(path.join(root,'production/channels/abyss-fieldnotes/evidence/publication-2026-11-20.json'));
  const episodes = state.episodes.filter(ep => /^D\d{3}$/.test(ep.id) &&
    (ep.active_build || ep.publication?.url || ep.id === state.active_episode || ep.id === checkpoint.episode)).map(ep => {
    const [videoId,video] = publicVideo(ep,feed.videos);
    const published = !!video || ['published','public_verified'].includes(ep.publication?.status);
    const build = ep.active_build || {};
    const url = videoId ? 'https://www.youtube.com/watch?v='+videoId : ep.publication?.url;
    const observed = historical.entries.find(e => e.episode === ep.id);
    const history = observed ? [{at:historical.at,views:observed.studio_views,source:'Studio'}] : [];
    for (const point of Object.values(video?.daily || {})) history.push({...point,source:'Feed YouTube'});
    history.sort((a,b) => a.at.localeCompare(b.at));
    return {id:ep.id,title:video?.title || ep.title,published,url,publishedAt:video?.published || ep.publication?.published_at,
      ready:!!build.upload_package && /^accepted/.test(build.owner_acceptance || ''),
      packageKey:build.delivery_manifest?.sha256 || build.upload_package?.sha256 || build.version,
      hasPackage:!!build.upload_package,review:build.review_page,master:build.review_file || ep.review_edit?.file,
      duration:build.duration_s || ep.review_edit?.duration_s,stage:ep.stage,history};
  });
  const tasks = channelBoard.read().tasks.filter(t => t.channelId === 'abyss')
    .sort((a,b) => b.updatedAt.localeCompare(a.updatedAt))
    .map(({title,stage,updatedAt}) => ({title,stage,updatedAt}));
  return {episodes, tasks, metrics:loadMetrics(), active:state.active_episode, next:checkpoint.next,
    checkpoint:checkpoint.status, feedAt:feed.checked_at, feedError};
}

function reject(message, status = 400) { throw Object.assign(new Error(message), {status}); }
function metric(value, max, integer) {
  if (value === null || value === undefined) return null;
  if (!Number.isFinite(value) || value < 0 || value > max || (integer && !Number.isSafeInteger(value)))
    reject('Số liệu nằm ngoài phạm vi hợp lệ.');
  return value;
}

export function recordMetrics(input) {
  if (!loadState().episodes.some(e => e.id === input.episode && /^D\d{3}$/.test(e.id)) ||
      !['24h','48h','7d'].includes(input.period)) reject('Kiểm tra mã tập và mốc đo.');
  const row = {episode:input.episode, period:input.period,
    views:metric(input.views,Number.MAX_SAFE_INTEGER,true),
    impressions:metric(input.impressions,Number.MAX_SAFE_INTEGER,true),
    ctr:metric(input.ctr,100,false), seconds:metric(input.seconds,Number.MAX_SAFE_INTEGER,true),
    retention:metric(input.retention,100,false)};
  if ([row.views,row.impressions,row.ctr,row.seconds,row.retention].every(n => n === null))
    reject('Nhập ít nhất một chỉ số từ Studio.');
  if (typeof input.note !== 'string' || input.note.length > 500) reject('Ghi chú tối đa 500 ký tự.');
  row.note = input.note.trim();
  const rows = [...loadMetrics()];
  const i = rows.findIndex(r => r.episode === row.episode && r.period === row.period);
  const old = rows[i];
  if (old && Object.keys(row).every(k => old[k] === row[k])) return old;
  if ((old?.version || 0) !== input.version) reject('Mốc này vừa thay đổi. Mở lại mốc đo để chỉnh sửa.',409);
  row.version = (old?.version || 0) + 1;
  row.at = new Date().toISOString();
  if (old) rows[i] = row;
  else rows.push(row);
  const temp = logFile + '.' + randomUUID() + '.tmp';
  try {
    fs.writeFileSync(temp, JSON.stringify(rows,null,2)+'\n', {flag:'wx'});
    fs.renameSync(temp,logFile);
  } finally {
    fs.rmSync(temp,{force:true});
  }
  return row;
}
