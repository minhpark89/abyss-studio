import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,copyFileSync,rmSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {registry,registryFile,updateRegistry,stages} from './registry.mjs';
import {matchRun} from './episodes.mjs';
import {readFileSync,writeFileSync} from 'node:fs';

test('a replacement voice processor does not archive the loudness master',()=>{
  const temp=mkdtempSync(path.join(os.tmpdir(),'abyss-mix-')),file=path.join(temp,'registry.json');
  try{
    const data=JSON.parse(readFileSync(registryFile,'utf8'));
    data.runtime_repos.push({name:'fixture-voice',stage:'audio_mixing',audio_role:'voice_polish',status:'TESTING'});
    writeFileSync(file,JSON.stringify(data));
    const {repos}=updateRegistry({name:'fixture-voice',status:'ACTIVE'},file);
    assert.equal(repos.find(r=>r.name==='spotify/pedalboard').status,'ARCHIVED');
    assert.equal(repos.find(r=>r.name==='slhck/ffmpeg-normalize').status,'ACTIVE');
    assert.equal(repos.find(r=>r.name==='fixture-voice').status,'ACTIVE');
  }finally{rmSync(temp,{recursive:true,force:true});}
});

test('promotion archives only the former active peer and rejects stale writes',()=>{
  const temp=mkdtempSync(path.join(os.tmpdir(),'abyss-board-')),file=path.join(temp,'registry.json');
  try{
    copyFileSync(registryFile,file);
    const before=registry(file);
    const target=before.repos.find(r=>r.status==='TESTING'&&before.repos.some(other=>other.stage===r.stage&&other.status==='ACTIVE'));
    const result=updateRegistry({name:target.name,status:'ACTIVE',version:before.version},file);
    const changed=result.repos.filter(r=>r.status!==before.repos.find(v=>v.name===r.name).status);
    assert.equal(changed.length,2);
    assert(changed.every(r=>r.stage===target.stage));
    assert.equal(result.repos.filter(r=>r.stage===target.stage&&r.status==='ACTIVE').length,1);
    assert.throws(()=>updateRegistry({name:target.name,status:'ARCHIVED',version:before.version},file),{status:409});
    for(const status of ['TESTING','ARCHIVED']){
      updateRegistry({name:target.name,status},file);
      assert.equal(registry(file).repos.find(r=>r.name===target.name).status,status);
    }
    const last=registry(file).version;
    assert.throws(()=>updateRegistry({name:'missing',status:'ACTIVE'},file),{status:404});
    assert.throws(()=>updateRegistry({name:target.name,status:'invalid'},file),{status:400});
    assert.equal(registry(file).version,last);
  }finally{rmSync(temp,{recursive:true,force:true});}
});
test('trace needs successful commands from a selected repo in every stage',()=>{
  const repos=Object.keys(stages).map(stage=>({stage,name:'test-'+stage,status:'TESTING',commit:'abc'}));
  const commands=repos.map(r=>({repo:r.name,stage:r.stage,commit:r.commit,command:'fixture-command',exit_code:0}));
  assert(matchRun({commands},repos).ok);
  for(const delta of [{exit_code:1},{commit:'old'},{repo:'undeclared'},{command:''}]){
    assert(!matchRun({commands:[{...commands[0],...delta},...commands.slice(1)]},repos).ok);
  }
  assert(!matchRun({commands:commands.slice(1)},repos).ok);
  assert(!matchRun({commands:[]},repos).ok);
  assert(!matchRun(null,repos).ok);
});

