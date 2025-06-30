(() => {
  const thread = document.getElementById('disqus_thread');
  if (!thread) return console.warn('No disqus_thread found');
  
  document.body.innerHTML = '';
  
  document.body.appendChild(thread);
  console.log('ONLY disqus_thread remains');
})();
