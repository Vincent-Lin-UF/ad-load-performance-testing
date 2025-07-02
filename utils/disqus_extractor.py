import asyncio
import re
from urllib.parse import urlparse
from typing import Tuple

from pydoll.browser.chromium   import Chrome
from pydoll.browser.options    import ChromiumOptions
from pydoll.commands.page_commands import PageCommands


async def _extract_disqus_info(tab, url: str) -> Tuple[str, str]:
    await tab._execute_command(PageCommands.navigate(url))

    js_poll = f"""
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
    """
    
    resp = await tab._execute_command({
        "method": "Runtime.evaluate",
        "params": {
            "expression":   js_poll,
            "awaitPromise": True,
            "returnByValue": True
        }
    })
    
    if not resp["result"]["result"]["value"]:
        print("Disqus globals didn't appear within 3s -> falling back early")

    js_cfg = """
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
          const m = s.src.match(/https?:\\/\\/([^.]+)\\.disqus\\.com\\/embed\\.js/);
          if (m) cfg.forum = m[1];
        }
      }
      return cfg;
    })()
    """
    
    resp = await tab._execute_command({
        "method": "Runtime.evaluate",
        "params": { "expression": js_cfg, "returnByValue": True }
    })
    
    cfg = resp["result"]["result"]["value"]

    if not cfg["forum"] or not cfg["identifier"]:
        html_resp = await tab._execute_command({
            "method": "Runtime.evaluate",
            "params": {
                "expression":   "document.documentElement.outerHTML",
                "returnByValue": True
            }
        })
        html = html_resp["result"]["result"]["value"]

        if not cfg["forum"]:
            m = re.search(r'https://([^.]+)\.disqus\.com/embed\.js', html)
            if m: cfg["forum"] = m.group(1)

        if not cfg["identifier"]:
            m = re.search(r'this\.page\.identifier\s*=\s*[\'"]([^\'"]+)[\'"]', html)
            if m: cfg["identifier"] = m.group(1)

    if not cfg["identifier"]:
        m = re.search(r'/([^/]+)/?$', url)
        if m: cfg["identifier"] = m.group(1)

    if not cfg["forum"]:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        cfg["forum"] = host.split(".")[0]

    return cfg["forum"], cfg["identifier"]


async def fetch_disqus_config(url: str, headless: bool = True) -> Tuple[str, str]:
    options = ChromiumOptions()
    options.add_argument("--headless=new")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    
    print("Extracting Disqus config from page…")

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        return await _extract_disqus_info(tab, url)

