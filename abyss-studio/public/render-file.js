export function renderActions(file,notify) {
  const group = document.createElement('span');
  group.className = 'render-actions';
  for (const [action,label] of [['reveal','Hiện trong thư mục'],['path','Chép đường dẫn MP4']]) {
    const button = document.createElement('button');
    button.type = 'button';button.className='quiet';button.textContent=label;
    button.onclick = async () => {
      button.disabled=true;
      try {
        const res=await fetch('/api/studio/render-file',{method:'POST',headers:{'Content-Type':'application/json','X-Abyss-Client':'1'},body:JSON.stringify({file,action})});
        const result=await res.json();
        if (!res.ok) throw Error(result.error);
        if (action==='reveal') notify(result.path);
        else {
          try {await navigator.clipboard.writeText(result.path);notify('Đã chép đường dẫn MP4.');}
          catch {notify(result.path);}
        }
      } catch(e){notify(e.message);}
      finally {button.disabled=false;}
    };
    group.append(button);
  }
  return group;
}
