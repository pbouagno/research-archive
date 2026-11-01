(function(){
  // Index: simple search over banners
  var q=document.getElementById('q');
  if(q){
    var rows=[].slice.call(document.querySelectorAll('.banner')),count=document.getElementById('count'),empty=document.getElementById('empty');
    var update=function(){
      var terms=q.value.toLowerCase().split(/\s+/).filter(Boolean),n=0;
      rows.forEach(function(r){var h=r.dataset.search,ok=terms.every(function(t){return h.indexOf(t)>=0;});r.hidden=!ok;if(ok)n++;});
      count.textContent=terms.length?n+' of '+rows.length+' reports':'';
      empty.hidden=n>0;
    };
    q.addEventListener('input',update);update();
  }
  // Detail: filter extracted links
  var lf=document.getElementById('lf');
  if(lf){
    var items=[].slice.call(document.querySelectorAll('.link-list li'));
    lf.addEventListener('input',function(){var v=lf.value.toLowerCase();items.forEach(function(li){li.hidden=li.textContent.toLowerCase().indexOf(v)<0;});});
  }
})();
