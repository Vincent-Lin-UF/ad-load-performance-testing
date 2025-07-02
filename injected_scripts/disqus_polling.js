new Promise(resolve => {{
    const start = Date.now();
    (function check() {{
    if (window.disqus_shortname || window.disqus_identifier) {{
        return resolve(true);
    }}
    if (Date.now() - start > 3000) {{
        return resolve(false);
    }}
    setTimeout(check, 100);
    }})();
}})