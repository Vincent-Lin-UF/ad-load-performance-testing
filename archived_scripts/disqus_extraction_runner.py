#!/usr/bin/env python3
import asyncio
import sys
import re

from pydoll.browser.chromium import Chrome
from pydoll.browser.options   import ChromiumOptions
from pydoll.commands.page_commands import PageCommands

from urllib.parse import urlparse

async def wait_for_disqus_ready(tab, max_wait_ms=3000, poll_interval_ms=100):
    """
    Poll every poll_interval_ms until window.disqus_shortname or
    window.disqus_identifier appears, or until max_wait_ms has elapsed.
    Returns True if Disqus appeared, False on timeout.
    """
    js = f"""
    new Promise(resolve => {{
      const start = Date.now();
      (function check() {{
        if (window.disqus_shortname || window.disqus_identifier) {{
          return resolve(true);
        }}
        if (Date.now() - start > {max_wait_ms}) {{
          return resolve(false);
        }}
        setTimeout(check, {poll_interval_ms});
      }})();
    }})
    """
    resp = await tab._execute_command({
      "method": "Runtime.evaluate",
      "params": {
        "expression": js,
        "awaitPromise": True,
        "returnByValue": True
      }
    })
    return resp["result"]["result"]["value"]



async def extract_disqus_info(tab, url):
    await tab._execute_command(PageCommands.navigate(url))
    # await tab._wait_page_load()
    # instead of: await asyncio.sleep(2)
    ready = await wait_for_disqus_ready(tab, max_wait_ms=3000)
    if not ready:
        print("⚠️  Disqus globals didn’t appear within 3 s—falling back early")


    # 1) Try pure JS extraction
    js = """
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
      "params": { "expression": js, "returnByValue": True }
    })
    cfg = resp["result"]["result"]["value"]

    # 2) If anything’s still missing, regex the outerHTML
    if not cfg["forum"] or not cfg["identifier"]:
      html_resp = await tab._execute_command({
        "method": "Runtime.evaluate",
        "params": { "expression": "document.documentElement.outerHTML", "returnByValue": True }
      })
      html = html_resp["result"]["result"]["value"]

      if not cfg["forum"]:
        m = re.search(r'https://([^.]+)\.disqus\.com/embed\.js', html)
        if m: cfg["forum"] = m.group(1)

      if not cfg["identifier"]:
        m = re.search(r'this\.page\.identifier\s*=\s*[\'"]([^\'"]+)[\'"]', html)
        if m: cfg["identifier"] = m.group(1)

    # 3) Fallback to last URL segment for identifier
    if not cfg["identifier"]:
        m = re.search(r'/([^/]+)/?$', url)
        if m:
            cfg["identifier"] = m.group(1)

    # 4) If forum still missing, use just the domain’s base name
    if not cfg["forum"]:
        parsed = urlparse(url)
        host   = parsed.netloc.lower()
        # strip www.
        if host.startswith("www."):
            host = host[4:]
        # take the part before the first dot
        cfg["forum"] = host.split(".")[0]
        print(f"ℹ️  No Disqus forum found; using domain base as forum: '{cfg['forum']}'")

    return cfg


async def main(url):
    opts = ChromiumOptions()
    # opts.add_argument('--headless=new')   # if you want headless

    async with Chrome(options=opts) as browser:
        # **This line actually launches Chrome** and returns the “default” tab
        tab = await browser.start()

        info = await extract_disqus_info(tab, url)
        print(f"Forum:      {info['forum']}")
        print(f"Identifier: {info['identifier']}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_disqus.py <URL>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
