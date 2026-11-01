(function(){
  var f=document.querySelector('.ref-filter');if(!f)return;
  var items=[].slice.call(document.querySelectorAll('.ref-list li'));
  f.addEventListener('input',function(){var v=f.value.toLowerCase();items.forEach(function(li){li.style.display=li.textContent.toLowerCase().indexOf(v)>=0?'':'none';});});
  if(matchMedia('(max-width:860px)').matches){var d=document.querySelector('.toc details');if(d)d.removeAttribute('open');}
})();
