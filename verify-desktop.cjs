// Start the actual desktop entry point against a separate loopback server.
const path=require('node:path'),fs=require('node:fs'),assert=require('node:assert/strict');
const {createRequire}=require('node:module'),{spawn}=require('node:child_process');
const studio=path.join(__dirname,'abyss-studio'),requireStudio=createRequire(path.join(studio,'package.json'));
(async()=>{
 const port=4388,origin='http://127.0.0.1:'+port,env={...process.env,NATIVE_STUDIO_PORT:String(port)};
 delete env.ELECTRON_RUN_AS_NODE;
 const server=spawn(process.execPath,['native-server.js'],{cwd:studio,env,windowsHide:true,stdio:'ignore'});let app;
 try{
   let up=false;
   for(let n=0;n<28;n++){if(server.exitCode!==null)throw Error('Server exited');try{up=(await fetch(origin+'/fieldnotes')).ok}catch{}if(up)break;await new Promise(r=>setTimeout(r,180));}
   assert(up);
   app=await requireStudio('playwright')._electron.launch({executablePath:requireStudio('electron'),args:[path.join(studio,'desktop/main.cjs')],env});
   const page=await app.firstWindow();await page.waitForURL(origin+'/**',{timeout:30000});
   const result=await page.evaluate(async()=>{
      const get=async path=>(await fetch(path)).json();
      const [board,state,registry]=await Promise.all(['/api/studio/channels','/api/studio/fieldnotes','/api/registry'].map(get));
      return {origin:location.origin,channels:board.channels.map(c=>c.name),active:state.active,integrations:registry.repos.length};
   });
   assert(result.channels.includes('Second Bell Pictures')&&result.channels.includes('Abyss Fieldnotes')&&result.active==='D007'&&result.integrations>0);
   await page.goto(origin+'/fieldnotes?episode=D007');await page.getByText(/This Deep-Sea Hunter Is a Colony/i).first().waitFor({state:'attached',timeout:20000});
   console.log(JSON.stringify(result));
 }finally{if(app)await app.close();server.kill();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});

