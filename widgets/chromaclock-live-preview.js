(function () {
  'use strict';
  const STYLES = ['neon','prism','starfield','matrix','fire','horizon','binary','minimal','pulse','wave','aurora','rain'];
  const COLORS = {cyan:'#23e6ff',magenta:'#ff41b4',amber:'#ffba38',green:'#4cff87'};
  const esc = s => String(s).replace(/[^a-zA-Z0-9_-]/g,'_');
  function run(container, config, value, options) {
    const id = esc(options.fieldId || container.id);
    const holder = document.createElement('div');
    holder.className = 'space-y-2';
    const heading = document.createElement('div');
    heading.textContent = 'Live Clock Preview · 5 × P5 (320 × 32)';
    heading.style.fontWeight = '600';
    const canvas = document.createElement('canvas');
    canvas.width = 320; canvas.height = 32;
    canvas.style.cssText = 'width:100%;max-width:960px;display:block;background:#000;border:1px solid #4b5563;border-radius:6px;image-rendering:pixelated';
    canvas.setAttribute('aria-label','Live ChromaClock Wide preview');
    const note = document.createElement('p');
    note.style.cssText = 'font-size:12px;opacity:.75;margin-top:5px';
    note.textContent = 'Updates before saving; your physical display changes only after Save. Preview uses browser canvas and approximates the Pillow renderer.';
    const status = document.createElement('p');
    status.style.cssText = 'font-size:12px;opacity:.85;margin-top:4px';
    holder.append(heading,canvas,status,note);
    container.replaceChildren(holder);
    const context=canvas.getContext('2d');
    if (!context) {status.textContent='Canvas unavailable';return;}
    const form=container.closest('form') || container.parentElement;
    const find = name => {
      const fields = document.querySelectorAll('input[name],select[name]');
      for(const el of fields) if(el.name === name || el.name.endsWith('.'+name)) return el;
      return null;
    };
    function read(name, fallback){
      const el=find(name);
      if(!el) return fallback;
      return el.type==='checkbox' ? el.checked : el.value;
    }
    function color(h){return 'hsl('+((h%360+360)%360)+' 95% 62%)';}
    function draw(){
      if(!container.isConnected)return;
      const t=Date.now()/1000,w=320,h=32;
      let style=read('style','cycle');
      const interval=Math.max(5,Number(read('cycle_seconds',20))||20);
      if(style==='cycle')style=STYLES[Math.floor(t/interval)%STYLES.length];
      if(read('preview_mode',false))style=read('preview_style','neon');
      if(!STYLES.includes(style))style='neon';
      const palette=read('palette','rainbow');
      const a=COLORS[palette]||color(t*4.8),b=color(t*4.8+100);
      const brightness=Math.max(.15,Math.min(1,Number(read('brightness',.85))||.85));
      const ctx=context;ctx.clearRect(0,0,w,h);ctx.fillStyle='#000';ctx.fillRect(0,0,w,h);
      for(let x=0;x<w;x++){
        if(Math.abs(x-w/2)<70)continue;
        const wave=Math.sin(x*.08+t);
        ctx.fillStyle=style==='matrix'?'#23ba60':style==='fire'?'#ff7721':style==='aurora'?'#42efa7':style==='prism'?color(x*1.1+t*9):a;
        ctx.globalAlpha=.55*brightness;
        let y=Math.floor(16+wave*7);
        if(['neon','prism'].includes(style)){ctx.fillRect(x,1,1,2);ctx.fillRect(x,29,1,2);}
        else if(style==='starfield'){if(x%5===0)ctx.fillRect(x,(x*23+7)%h,1,1);}
        else if(style==='matrix'||style==='rain'){if(x%7===0)ctx.fillRect(x,Math.floor((t*10+x*13)%38)-5,1,5);}
        else if(style==='fire'||style==='horizon'){ctx.fillRect(x,y,1,h-y);}
        else if(style==='binary'){if(x%8===0)for(let j=0;j<4;j++)if((x+j+Math.floor(t))%3===0)ctx.fillRect(x,3+j*7,3,3);}
        else if(style==='pulse')ctx.fillRect(x,Math.min(y,16),1,Math.abs(y-16)+1);
        else if(style==='wave'||style==='aurora')ctx.fillRect(x,y,1,2);
        else if(x%12===0)ctx.fillRect(x,h-2,1,1);
      }
      ctx.globalAlpha=1;
      const timezone=read('timezone','America/New_York');
      let n=new Date(),hour=n.getHours(),minute=n.getMinutes(),sec=n.getSeconds(),dateLabel='';
      try{
        const parts=new Intl.DateTimeFormat('en-US',{timeZone:timezone,hour:'numeric',minute:'numeric',second:'numeric',hour12:false}).formatToParts(n);
        const part=k=>Number(parts.find(p=>p.type===k)?.value||0);
        hour=part('hour')%24;minute=part('minute');sec=part('second');
        dateLabel=new Intl.DateTimeFormat('en-US',{timeZone:timezone,weekday:'short',month:'short',day:'numeric'}).format(n).toUpperCase();
      }catch(e){dateLabel=n.toDateString().toUpperCase();}
      const h24=read('use_24h',false), hstr=String(h24?hour:(hour%12||12));
      const text=hstr+':'+String(minute).padStart(2,'0');
      const dateOn=read('show_date',true),secOn=read('show_seconds',true);
      const maxW=160;
      let size=dateOn?23:27;
      ctx.font='bold '+size+'px monospace';
      while(ctx.measureText(text).width>maxW&&size>8){size--;ctx.font='bold '+size+'px monospace';}
      ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=a;
      if(read('glow',true)){ctx.globalAlpha=.25;ctx.fillText(text,161,dateOn?12:16);ctx.fillText(text,159,dateOn?12:16);ctx.globalAlpha=1;}
      ctx.fillText(text,160,dateOn?12:16);
      if(secOn){ctx.font='bold 8px monospace';ctx.fillStyle=b;ctx.fillText(String(sec).padStart(2,'0'),230,8);ctx.fillStyle=a;ctx.fillRect(0,31,Math.floor(w*sec/60),1);}
      if(dateOn){ctx.font='bold 7px monospace';ctx.fillStyle='#cdd5e6';ctx.fillText(dateLabel,160,27);}
      status.textContent='Previewing: '+style+' · '+w+'×'+h+' · '+(h24?'24h':'12h')+' · '+timezone;
      ctx.globalAlpha=1;
    }
    let timer=setInterval(()=>{if(!container.isConnected){clearInterval(timer);return;} draw();},250);
    form.addEventListener('input',draw);
    form.addEventListener('change',draw);
    draw();
  }
  if(window.LEDMatrixWidgets){
    window.LEDMatrixWidgets.register('chromaclock-live-preview',{
      name:'Live ChromaClock Preview',
      version:'1.0.0',
      render:run,
      getValue:function(){return 'live';},
      setValue:function(){},
      handlers:{}
    });
  }
})();