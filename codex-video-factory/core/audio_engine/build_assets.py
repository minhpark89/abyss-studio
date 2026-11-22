"""Compose the factory's original score and Foley library. No sample packs or network."""
import json
import sys
import subprocess
import tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

FACTORY = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(FACTORY))
from core.project import FF, save, sha

ASSETS=FACTORY/"core/assets"
RATE=32000
CC0="https://creativecommons.org/publicdomain/zero/1.0/"

# MIDI voicings and rhythmic phrases, composed for these cues.
SCORES={
    "tense_pulse":("karma-drama",82,[[50,57,60,65],[46,53,57,62],[48,55,58,64],[45,52,58,61]],0),
    "dark_escalation":("karma-drama",101,[[38,45,50,57],[39,46,55,58],[43,50,53,60],[45,52,58,61]],1),
    "karma_payoff":("karma-drama",76,[[58,65,69,74],[55,62,65,70],[53,60,64,69],[58,62,65,72]],2),
    "curiosity_ambient":("hybrid-explainer",72,[[60,67,71,74],[57,64,67,74],[53,60,64,71],[55,62,69,72]],3),
    "tech_reveal":("hybrid-explainer",110,[[50,57,62,69],[55,62,67,71],[53,60,64,69],[48,55,60,67]],4),
}
EFFECTS={"riser_2s":2,"bass_drop":1.45,"whoosh":.65,"crowd_gasp":1.25,"room_tone":14}

def band(samples,lo,hi):
    return sosfilt(butter(3,[lo,hi],btype="bandpass",fs=RATE,output="sos"),samples)

def tone(key,seconds,instrument):
    t=np.arange(round(seconds*RATE))/RATE
    pitch=440*2**((key-69)/12)
    phase=2*np.pi*t*pitch
    if instrument=="bow":
        vibrato=.16*np.sin(2*np.pi*4.7*t)
        body=sum(np.sin(i*phase+i*vibrato)/i**1.7 for i in range(1,6))
        env=np.minimum(1,t/.32)*np.minimum(1,(seconds-t)/.48)*(.78+.22*np.sin(np.pi*t/seconds))
    elif instrument=="felt":
        body=sum(w*np.sin(phase*h*(1+.00012*h*h)) for h,w in [(1,1),(2,.43),(3,.19),(4,.09)])
        env=(1-np.exp(-t*105))*np.exp(-2.3*t)*np.minimum(1,(seconds-t)/.08)
    else:
        body=np.sin(phase)+.35*np.sin(phase*2)*np.exp(-8*t)+.18*np.sin(phase*3)*np.exp(-12*t)
        env=(1-np.exp(-t*160))*np.exp(-6*t)*np.minimum(1,(seconds-t)/.075)
    return (body*env).astype("float32")

def put(bus,signal,at,gain,pan):
    offset=round(at*RATE); n=min(len(signal),len(bus)-offset)
    if n<=0:return
    left,right=np.cos((pan+1)*np.pi/4),np.sin((pan+1)*np.pi/4)
    bus[offset:offset+n,0]+=signal[:n]*gain*left
    bus[offset:offset+n,1]+=signal[:n]*gain*right

def compose(name):
    _,tempo,chords,style=SCORES[name]
    beat=60/tempo; bars=16; duration=bars*4*beat
    mix=np.zeros((round(duration*RATE),2),dtype="float32")
    rng=np.random.default_rng(20261121+style)
    for bar in range(bars):
        chord=chords[bar%4];base=bar*4*beat
        swell=(.82+.12*np.sin(2*np.pi*bar/8))*(.86+.09*(bar//4))
        for i,k in enumerate(chord):
            put(mix,tone(k+(12 if style==3 else 0),3.96*beat,"bow"),base,.075*swell,(-.64+i*.42))
        bass_key=chord[0]-(12 if chord[0]>=48 else 0)
        for b in ([0,1.5,2,3.5] if style==1 else [0,2.5]):
            put(mix,tone(bass_key,.82*beat,"pizz"),base+b*beat,.45*swell,-.13)
        if style==1:
            for b in np.arange(0,4,.5):
                pulse=tone(chord[1],.43*beat,"pizz")
                put(mix,pulse,base+b*beat,.15*(1 if b%1==0 else .6),.27)
            for b in (0,2,2.27):
                tt=np.arange(int(.29*RATE))/RATE
                thump=np.sin(2*np.pi*(43*tt+.75*(1-np.exp(-26*tt))))*(1-np.exp(-100*tt))*np.exp(-17*tt)
                put(mix,thump,base+b*beat,.22,0)
        else:
            pattern=[[0,2,1,3],[0,1,3,2],[3,2,1,2],[1,3,2,0],[0,2,1,3]][style]
            onsets=[.5,1.75,2.5,3.5] if style in (0,3) else [0,1.5,2.3,3.25]
            for index,(b,degree) in enumerate(zip(onsets,pattern)):
                if bar%4==3 and index==3:continue
                key=chord[(degree+(1 if bar//4%2 else 0))%4]+(12 if style in (2,3,4) else 0)
                put(mix,tone(key,1.9*beat,"felt" if style in (2,3) else "pizz"),
                    base+b*beat+float(rng.uniform(0,.012)),.22*swell if style!=3 else .13,(-1)**index*.31)
        if style==2 and bar%2==0:
            put(mix,tone(chord[3]+5,2.6*beat,"bow"),base+beat,.085,.4)
    for lag,gain in ((.053,.12),(.119,.09),(.197,.045)):
        d=round(lag*RATE);mix[d:]+=mix[:-d,::-1]*gain
    fade=round(.32*RATE)
    mix[:fade]*=np.linspace(0,1,fade)[:,None];mix[-fade:]*=np.linspace(1,0,fade)[:,None]
    return mix*(.78/max(np.max(abs(mix)),.01))

def effect(name,duration):
    rng=np.random.default_rng(240+list(EFFECTS).index(name));n=round(duration*RATE)
    t=np.arange(n)/RATE;u=t/duration;noise=rng.normal(0,.3,n)
    if name=="bass_drop":
        a=np.sin(2*np.pi*(36*t+3.1*(1-np.exp(-8*t))))*(1-np.exp(-95*t))*np.exp(-4*t)
        a+=band(noise,70,400)*np.exp(-26*t)
    elif name=="riser_2s":
        a=band(noise,420,5800)*u**2+.13*np.sin(2*np.pi*(190*t+100*t*t))*u**2
    elif name=="whoosh":a=band(noise,460,6400)*np.sin(np.pi*u)**2
    elif name=="crowd_gasp":
        a=np.zeros(n)
        for j in range(7):
            start=.03+j*.046
            v=np.maximum(0,t-start)
            air=band(rng.normal(0,.48,n),520+j*54,2160+j*104)
            a+=air*(1-np.exp(-v*24))*np.exp(-v*(3.4+j*.18))
    else:a=band(noise,90,3900)*.12+.0007*np.sin(2*np.pi*60*t)
    a*=np.clip(t/.012,0,1)*np.clip((duration-t)/.09,0,1)
    return (a*(.68 if name!="room_tone" else .12)/max(np.max(abs(a)),1e-5)).astype("float32")

def main():
    items={};cache=ASSETS/"sfx_cache";cache.mkdir(parents=True,exist_ok=True)
    origin=dict(origin="original procedural composition",author="Second Bell Studio",license="CC0-1.0",license_url=CC0)
    with tempfile.TemporaryDirectory(prefix="score-") as tmp:
        wav=Path(tmp)/"score.wav"
        for name,(niche,_,__,___) in SCORES.items():
            path=ASSETS/"bgm"/niche/(name+".mp3");path.parent.mkdir(parents=True,exist_ok=True)
            score=compose(name);sf.write(wav,score,RATE,subtype="PCM_24")
            subprocess.run([FF,"-v","error","-nostdin","-y","-i",str(wav),"-map_metadata","-1","-codec:a","libmp3lame","-b:a","192k",str(path)],check=True)
            items[name]=dict(**origin,path=path.relative_to(ASSETS).as_posix(),sha256=sha(path),seconds=len(score)/RATE,kind="music",niche=niche)
    for name,duration in EFFECTS.items():
        path=cache/(name+".wav")
        sf.write(path,effect(name,duration),RATE,subtype="PCM_24")
        items[name]=dict(**origin,path=path.relative_to(ASSETS).as_posix(),sha256=sha(path),seconds=duration,kind="sfx")
    index=cache/"sfx_index.json"
    stored=json.loads(index.read_text(encoding="utf-8-sig")) if index.exists() else {}
    stored.update({k:v for k,v in items.items() if v["kind"]=="sfx" and k not in stored})
    save(index,stored)
    save(ASSETS/"audio_manifest.json",dict(version=1,sample_rate=RATE,aliases={"tense_bed":"tense_pulse","twist_riser":"riser_2s","escalation":"dark_escalation","payoff":"karma_payoff"},tracks=items))
    print(len(items),"original music and effect assets")

if __name__=="__main__":main()
