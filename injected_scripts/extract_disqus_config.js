  (() => {
    const cfg = { identifier: null, forum: null };
    if (window.disqus_shortname)  cfg.forum      = window.disqus_shortname;
    if (window.disqus_identifier) cfg.identifier = window.disqus_identifier;
    if (typeof window.disqus_config === 'function') {
      try { window.disqus_config.call(cfg) } catch {}
    }
    if (!cfg.forum) {
      const s = document.querySelector('script[src*=".disqus.com/embed.js"]');
      if (s) {
        const m = s.src.match(/https?:\/\/([^.]+)\.disqus\.com\/embed\.js/);
        if (m) cfg.forum = m[1];
      }
    }
    return cfg;
  })()