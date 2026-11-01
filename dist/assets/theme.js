(function(){
  var root=document.documentElement,btn=document.querySelector('.theme-toggle');
  if(!btn)return;
  function current(){return root.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');}
  btn.addEventListener('click',function(){var t=current()==='dark'?'light':'dark';root.dataset.theme=t;try{localStorage.setItem('theme',t);}catch(e){}});
})();
