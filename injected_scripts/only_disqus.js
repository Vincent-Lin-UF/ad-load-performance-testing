// only_disqus.js
;(function(){
  const d = document;
  const shortname = location.hostname.split('.')[0];
  // 1) inject the embed.js script immediately
  const s = d.createElement('script');
  s.src = `https://${shortname}.disqus.com/embed.js`;
  s.setAttribute('data-timestamp', +new Date());
  (d.head || d.body).appendChild(s);

  // 2) watch for the iframe inside #disqus_thread
  const observer = new MutationObserver((mutations, obs) => {
    const thread = d.getElementById('disqus_thread');
    if (!thread) return;
    const iframe = thread.querySelector('iframe');
    if (!iframe) return;

    // once we see it, prune everything else
    obs.disconnect();
    d.body.innerHTML = '';
    d.body.appendChild(thread);
  });

  // start observing as soon as possible
  observer.observe(d.documentElement, { childList: true, subtree: true });
})();
