def srt_time(t):
    m=round(t*1000);h,m=divmod(m,3600000);n,m=divmod(m,60000);s,m=divmod(m,1000)
    return f'{h:02}:{n:02}:{s:02},{m:03}'
def cues(words):
    groups=[];start=0
    for i,w in enumerate(words):
        current=words[start:i+1];line=' '.join(a['word'] for a in current)
        nextw=words[i+1] if i+1<len(words) else None
        if not nextw or w['word'].endswith(('.','?','!')) or len(line)+1+len(nextw['word'])>53 or (len(line)>23 and w['word'].endswith((',', ';'))) or w['end']-current[0]['start']>3.55 or nextw['start']-w['end']>.49:
            groups.append(current);start=i+1
    for i in range(len(groups)-1,0,-1):
        a,c=groups[i-1:i+1]
        if c[-1]['end']-c[0]['start']<.78 and not a[-1]['word'].endswith(('.','?','!')):
            if len(' '.join(w['word'] for w in a+c))<=55:
                a.extend(c);groups.pop(i)
            else:
                while len(a)>3 and (len(c)<3 or c[-1]['end']-c[0]['start']<.88):
                    c.insert(0,a.pop())
    return [dict(a=c[0]['start'],b=min(c[-1]['end']+.17,groups[i+1][0]['start']-.012 if i+1<len(groups) else 999),text=' '.join(w['word'] for w in c)) for i,c in enumerate(groups)]
