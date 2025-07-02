import re
from urllib.parse import urlparse
from typing import Tuple

from pydoll.commands.page_commands import PageCommands

from loaders.script_loader import load_script

async def extract_disqus_info(tab, url: str) -> Tuple[str, str]:
    await tab._execute_command(PageCommands.navigate(url))
    js_poll = load_script("disqus_polling.js")
    
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
      js_cfg = load_script("extract_disqus_config.js")
    
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