import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {requireResearch} from '../../../../lib/config.js';
const url='http://127.0.0.1:4320/production/episodes/D007/opening-v1/delivery/review.html';
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'abyss-d007-opening-player-'));
fs.writeFileSync(path.join(tmp,'native.cjs'),"const {app,BrowserWindow}=require('electron');app.setPath('userData',__dirname+'/profile');app.commandLine.appendSwitch('autoplay-policy','no-user-gesture-required');app.commandLine.appendSwitch('disable-background-timer-throttling');app.commandLine.appendSwitch('disable-renderer-backgrounding');app.whenReady().then(()=>{global.w=new BrowserWindow({show:false,width:1150,height:800,webPreferences:{backgroundThrottling:false}});w.loadURL('about:blank');});");
const env={...process.env};delete env.ELECTRON_RUN_AS_NODE;
const app=await requireResearch('playwright')._electron.launch({executablePath:requireResearch('electron'),args:[path.join(tmp,'native.cjs')],env});
try{
 const pg=await app.firstWindow(),errors=[];pg.on('pageerror',e=>errors.push(e.message));
 const response=await pg.goto(url);assert.equal(response.status(),200);
 const v=pg.locator('video');await pg.waitForFunction(()=>document.querySelector('video').readyState>=1,null,{timeout:18000});
 await pg.setViewportSize({width:390,height:844});assert(await pg.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await pg.setViewportSize({width:1280,height:800});
 const target=Number(await pg.locator('button[data-time]').last().getAttribute('data-time'));
 await pg.locator('button[data-time]').last().click();
 await pg.waitForFunction(target=>Math.abs(document.querySelector('video').currentTime-target)<1.1,target,{timeout:8000});
 await pg.waitForFunction(()=>{const v=document.querySelector('video');return !v.paused&&!v.seeking&&v.readyState>=3;});
 await pg.evaluate(async()=>{
   const v=document.querySelector('video');v.pause();v.currentTime=0;v.playbackRate=1;
   const audio=new AudioContext(),an=audio.createAnalyser(),gain=audio.createGain();gain.gain.value=0;an.fftSize=1024;
   const input=audio.createMediaElementSource(v);input.connect(an);an.connect(gain);gain.connect(audio.destination);window.audioGraph={audio,input,an,gain};await audio.resume();
   const samples=new Float32Array(1024);window.bins=[];window.started=Date.now();window.levelCount=0;
   const key=setInterval(()=>{an.getFloatTimeDomainData(samples);const i=Math.floor(v.currentTime/10);const level=Math.sqrt(samples.reduce((n,x)=>n+x*x,0)/samples.length);window.bins[i]=Math.max(window.bins[i]||0,level);window.levelCount++;},250);
   v.addEventListener('ended',()=>clearInterval(key),{once:true});await v.play();
 });
 while(!(await v.evaluate(v=>v.ended))){
   const prev=await v.evaluate(v=>v.currentTime);
   await pg.waitForFunction(prev=>{const v=document.querySelector('video');return v.ended||v.error||v.currentTime>=prev+25;},prev,{timeout:42000});
   const current=await v.evaluate(v=>({at:v.currentTime,ended:v.ended,error:v.error?.message||null,readings:window.levelCount,bins:window.bins,audio_context:window.audioGraph.audio.state,elapsed_s:(Date.now()-window.started)/1000}));assert(!current.error);
   fs.writeFileSync(new URL('./qa/playback-progress.json',import.meta.url),JSON.stringify(current));console.log(current.at.toFixed(1),'s',current.audio_context,current.readings);
 }
 const report=await pg.evaluate(()=>{const v=document.querySelector('video'),q=v.getVideoPlaybackQuality();
   return {ended:v.ended,rate:v.playbackRate,seconds:v.duration,wall_seconds:(Date.now()-window.started)/1000,total_frames:q.totalVideoFrames,dropped:q.droppedVideoFrames,
   sound_readings:window.levelCount,peak_rms_by_10s:window.bins,error:v.error?.message||null};});
 const hash=createHash('sha256');for await(const data of fs.createReadStream(new URL('./delivery/D007-opening.mp4',import.meta.url)))hash.update(data);
 Object.assign(report,{sha256:hash.digest('hex'),review_url:url,mobile_layout:true,chapter_seek:true,page_errors:errors,audio_method:'Web Audio analyzer ahead of silent output gain',human_listening:'pending owner'});
 fs.writeFileSync(new URL('./qa/player.json',import.meta.url),JSON.stringify(report,null,2));
 assert(report.ended&&report.rate===1&&Math.abs(report.seconds-JSON.parse(fs.readFileSync(new URL("./timing.json",import.meta.url))).duration)<.09&&report.total_frames-report.dropped>report.seconds*23&&!report.error&&!errors.length);
 console.log('Player reached the last frame.',report.wall_seconds,'wall seconds;',report.sound_readings,'meter readings');
}finally{await app.close();}
