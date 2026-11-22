// Used by both the dashboard and the pre-submit check; upstream times are Unix seconds.
export function verifiedSession(a,now=Date.now()/1000){
 return a.enabled===true && a.ok===true && a.essential_ok===true &&
 (a.status==='active'||a.status==='cooldown'&&a.cooldown_until>0&&a.cooldown_until<=now) &&
 !(a.cooldown_until>now) && (!a.expires_at||a.expires_at>now);
}
export function acceptsNewVideo(a,now=Date.now()/1000){
 return verifiedSession(a,now)&&!a.video_paused&&!(a.quota?.found && a.quota.weekly_used_pct>=100 && (a.quota.extra_used_pct==null||a.quota.extra_used_pct>=100));
}
