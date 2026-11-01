(function(){
  var data=JSON.parse(document.getElementById('data').textContent);
  var projects=data.projects, cardsEl=document.getElementById('cards'), q=document.getElementById('q'),
      sortBtn=document.getElementById('sort'), tagbar=document.getElementById('tagbar'), countEl=document.getElementById('count');
  var params=new URLSearchParams(location.search);
  var state={q:params.get('q')||'',tags:new Set(params.getAll('tag')),desc:params.get('sort')!=='asc'};
  q.value=state.q;
  function esc(s){return String(s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  var counts={};projects.forEach(function(p){p.tags.forEach(function(t){counts[t]=(counts[t]||0)+1;});});
  var allTags=Object.keys(counts).sort(function(a,b){return counts[b]-counts[a]||a.localeCompare(b);});
  function renderTags(){
    tagbar.innerHTML='<button class="chip" data-tag="" aria-pressed="'+(state.tags.size===0)+'">All</button>'+
      allTags.map(function(t){return '<button class="chip" data-tag="'+esc(t)+'" aria-pressed="'+state.tags.has(t)+'">'+esc(t)+' <span class="muted">'+counts[t]+'</span></button>';}).join('');
  }
  function haystack(p){return [p.disclaimer||'',p.title,p.summary,p.tags.join(' '),(p.stats||[]).join(' '),p.date_label,p.doc,(p.related_files||[]).join(' ')].join(' ').toLowerCase();}
  function render(){
    var terms=state.q.toLowerCase().split(/\s+/).filter(Boolean);
    var list=projects.filter(function(p){
      if(state.tags.size){for(var t of state.tags){if(p.tags.indexOf(t)<0)return false;}}
      var h=haystack(p);return terms.every(function(w){return h.indexOf(w)>=0;});
    }).sort(function(a,b){return state.desc?b.date.localeCompare(a.date):a.date.localeCompare(b.date);});
    sortBtn.textContent=state.desc?'Newest first ↓':'Oldest first ↑';
    countEl.textContent=list.length+' of '+projects.length+' projects';
    cardsEl.innerHTML=list.length?list.map(function(p){
      return '<article class="card"><time datetime="'+esc(p.date)+'">'+esc(p.date_label)+'</time>'+
        '<h2><a href="'+esc(p.url)+'">'+esc(p.title)+'</a></h2>'+
        '<div class="tags">'+p.tags.map(function(t){return '<button class="tag" data-tag="'+esc(t)+'">'+esc(t)+'</button>';}).join('')+'</div>'+
        (p.disclaimer?'<p class="disclaimer" role="note"><strong>⚠ '+esc(p.disclaimer)+'</strong></p>':'')+
        '<p>'+esc(p.summary)+'</p>'+
        '<ul class="stats">'+(p.stats||[]).map(function(s){return '<li>'+esc(s)+'</li>';}).join('')+(p.links_found?'<li>'+p.links_found+' links extracted</li>':'')+'</ul>'+
        (p.model_url?'<a class="btn-primary" href="'+esc(p.model_url)+'" target="_blank" rel="noopener noreferrer">Open interactive model ↗</a>':'')+
        '<a class="open" href="'+esc(p.url)+'">'+(p.model_url?'Model summary →':'Read online →')+'</a>'+
        ((p.related_titles||[]).length?'<p class="muted" style="margin:0;font-size:13px">Related: '+p.related_titles.map(function(r){return '<a href="projects/'+esc(r.slug)+'/index.html">'+esc(r.title)+'</a>';}).join(' · ')+'</p>':'')+
        '<div class="downloads">'+p.downloads.map(function(d){return '<a class="dl" href="'+esc(d.href)+'" title="'+esc(d.name)+'" download><span class="ext ext-'+d.ext.toLowerCase()+'">'+esc(d.ext)+'</span>'+esc(d.name)+' <small>'+esc(d.size)+'</small></a>';}).join('')+'</div></article>';
    }).join(''):'<div class="empty">No projects match. Try clearing the search or tag filter.</div>';
    renderTags();
    var u=new URLSearchParams();if(state.q)u.set('q',state.q);state.tags.forEach(function(t){u.append('tag',t);});if(!state.desc)u.set('sort','asc');
    history.replaceState(null,'',location.pathname+(u.toString()?'?'+u:''));
  }
  function toggleTag(t){if(!t){state.tags.clear();}else if(state.tags.has(t)){state.tags.delete(t);}else{state.tags.add(t);}render();}
  tagbar.addEventListener('click',function(e){var b=e.target.closest('.chip');if(b)toggleTag(b.dataset.tag);});
  cardsEl.addEventListener('click',function(e){var b=e.target.closest('.tag');if(b){e.preventDefault();toggleTag(b.dataset.tag);}});
  q.addEventListener('input',function(){state.q=q.value;render();});
  sortBtn.addEventListener('click',function(){state.desc=!state.desc;render();});
  document.addEventListener('keydown',function(e){if(e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus();}});
  render();
})();
