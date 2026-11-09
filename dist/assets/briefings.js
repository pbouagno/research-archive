(function(){
  // Daily feeds index: full-text search + company chips (jobs). Shared by classic and v2 views.
  var q=document.getElementById('fq'),list=document.getElementById('flist');
  if(!q||!list)return;
  var rows=[].slice.call(list.children),count=document.getElementById('fcount'),empty=document.getElementById('fempty');
  var chips=[].slice.call(document.querySelectorAll('.chip[data-co]')),active=[];
  try{var p=new URLSearchParams(location.search);if(p.get('q'))q.value=p.get('q');}catch(e){}
  function update(){
    var terms=q.value.toLowerCase().split(/\s+/).filter(Boolean),n=0;
    rows.forEach(function(r){
      var h=r.getAttribute('data-search')||'',cos=r.getAttribute('data-cos')||'';
      var ok=terms.every(function(t){return h.indexOf(t)>=0;})&&active.every(function(c){return cos.indexOf(c)>=0;});
      r.hidden=!ok;if(ok)n++;
    });
    if(count)count.textContent=(terms.length||active.length)?n+' of '+rows.length+' shown':rows.length+' total';
    if(empty)empty.hidden=n>0;
  }
  chips.forEach(function(b){b.addEventListener('click',function(){
    var c=b.getAttribute('data-co'),on=b.getAttribute('aria-pressed')!=='true';
    b.setAttribute('aria-pressed',on?'true':'false');
    active=on?active.concat([c]):active.filter(function(x){return x!==c;});update();
  });});
  q.addEventListener('input',update);update();
})();

(function(){
  // Jobs company cards (added 2026-11-03): labelled trend lines drawn at the real container width,
  // and the "Earlier days" lists collapse on narrow screens. Data comes from data-jc-chart (built from the reports).
  var charts=[].slice.call(document.querySelectorAll('[data-jc-chart]'));
  var mores=[].slice.call(document.querySelectorAll('details.jc-more'));
  if(!charts.length&&!mores.length)return;
  function fmt(v){return v.toLocaleString('en-US');}
  function lab(d,prev,narrow){if(!narrow)return d;var m=d.split(' ')[0];return(!prev||prev.split(' ')[0]!==m)?d:d.split(' ')[1];}
  function draw(el){
    var cfg;try{cfg=JSON.parse(el.getAttribute('data-jc-chart'));}catch(e){return;}
    var pts=cfg.points||[],n=pts.length,W=el.clientWidth,H=150,top=30,bot=30;
    if(!W||n<1)return;
    var vals=pts.map(function(p){return p.v;}).filter(function(v){return typeof v==='number';});
    if(!vals.length)return;
    var lo=Math.min.apply(null,vals),hi=Math.max.apply(null,vals),span=(hi-lo)||1;lo-=span*.15;hi+=span*.15;span=hi-lo;
    var padX=Math.max(26,Math.min(40,W/n/2)),step=n>1?(W-2*padX)/(n-1):0,narrow=step<62;
    function X(i){return n>1?padX+i*step:W/2;}function Y(v){return top+(H-top-bot)*(1-(v-lo)/span);}
    var s='<svg class="jc-lc" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'" role="img" aria-label="'+(cfg.aria||'')+'">';
    s+='<line class="jc-grid-l" x1="0" x2="'+W+'" y1="'+(H-bot)+'" y2="'+(H-bot)+'"/>';
    var d='',first=-1,last=-1;
    pts.forEach(function(p,i){if(typeof p.v!=='number')return;d+=(first<0?'M':'L')+X(i).toFixed(1)+','+Y(p.v).toFixed(1);if(first<0)first=i;last=i;});
    if(last>first)s+='<path class="jc-area" d="'+d+'L'+X(last)+','+(H-bot)+'L'+X(first)+','+(H-bot)+'Z"/>';
    s+='<path class="jc-line" d="'+d+'"/>';
    var prev=null;
    pts.forEach(function(p,i){
      s+='<text class="jc-x" x="'+X(i)+'" y="'+(H-8)+'" text-anchor="middle">'+lab(p.d,prev,narrow)+'</text>';prev=p.d;
      if(typeof p.v!=='number')return;
      var pv=i>0?pts[i-1].v:null,nv=i<n-1?pts[i+1].v:null;
      var below=(typeof pv==='number'&&p.v<pv)&&(typeof nv!=='number'||p.v<nv)&&Y(p.v)+26<H-bot;
      s+='<circle r="4.5" class="'+(i===last?'jc-last':'')+'" cx="'+X(i)+'" cy="'+Y(p.v)+'"><title>'+p.d+': '+fmt(p.v)+'</title></circle>';
      s+='<text class="jc-v" x="'+X(i)+'" y="'+(below?Y(p.v)+24:Y(p.v)-11)+'" text-anchor="middle">'+fmt(p.v)+'</text>';
    });
    el.innerHTML=s+'</svg>';
  }
  var mq=window.matchMedia('(max-width: 961px)');
  function collapse(){mores.forEach(function(m){if(!m.hasAttribute('data-touched'))m.open=!mq.matches;});}
  mores.forEach(function(m){m.querySelector('summary').addEventListener('click',function(){m.setAttribute('data-touched','');});});
  function all(){charts.forEach(draw);}
  var t;window.addEventListener('resize',function(){clearTimeout(t);t=setTimeout(all,120);});
  if(mq.addEventListener)mq.addEventListener('change',collapse);
  collapse();all();
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(all);
})();
