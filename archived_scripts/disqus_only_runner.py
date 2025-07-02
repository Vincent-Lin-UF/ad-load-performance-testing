#!/usr/bin/env python3
import asyncio
import sys
import time
import base64

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.commands.fetch_commands import FetchCommands
from pydoll.commands.page_commands  import PageCommands
from pydoll_extensions import TabWrapper
from pydoll.constants import RequestStage

async def test_only_disqus(url: str):
    opts = ChromiumOptions()
    # comment out if you want to watch it:
    # opts.add_argument('--headless=new')

    async with Chrome(options=opts) as browser:
        tab = TabWrapper(await browser.start())

        # 1) Intercept all responses
        await tab._execute_command(
            FetchCommands.enable(
                handle_auth_requests=False,
                url_pattern="*",
                request_stage=RequestStage.RESPONSE
            )
        )

        async def on_paused(event):
            p     = event.get("params", event)
            rid   = p["requestId"]
            rtype = p.get("resourceType")
            rurl  = p.get("request", {}).get("url", "")

            # only hijack the top‑level HTML document
            if rtype == "Document" and rurl == url:
                # build a complete HTML page that loads Disqus:
                html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Comments</title>
</head>
<body>
  <div id="disqus_thread"></div>

  <script>
    var disqus_config = function () {{
      this.page.url        = '{url}';
      this.page.identifier = 'hitchins-proclaims-true-champion-status-after-stopping-george-kambosos';  // update per‑site!
      this.page.title      = document.title;
    }};
  </script>

  <script src="https://boxingnews24.disqus.com/embed.js" data-timestamp="{{timestamp}}"></script>
  <noscript>Please enable JavaScript to view the comments powered by Disqus.</noscript>
</body>
</html>
"""
                # insert a fresh timestamp
                html = html.replace(
                    "{timestamp}",
                    str(int(time.time()))
                )
                b64  = base64.b64encode(html.encode("utf-8")).decode()

                return await tab._execute_command(
                    FetchCommands.fulfill_request(
                        request_id    = rid,
                        response_code = 200,
                        response_headers=[{"name":"Content-Type","value":"text/html; charset=utf-8"}],
                        body          = b64,
                    )
                )

            # otherwise let it load normally
            await tab._execute_command(FetchCommands.continue_request(rid))

        # 2) wire up the interceptor
        await tab.on("Fetch.requestPaused", on_paused)

        # 3) navigate – your on_paused will fire and replace the document
        await tab._execute_command(PageCommands.navigate(url))
        await tab._wait_page_load()

        # 4) leave it open so you can see the comments
        print("✅ Disqus‑only page loaded. Press Ctrl+C to exit.")
        await asyncio.Event().wait()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test2.py <URL>")
        sys.exit(1)
    asyncio.run(test_only_disqus(sys.argv[1]))
