import time, base64, asyncio
from pydoll.browser.chromium      import Chrome
from pydoll.browser.options       import ChromiumOptions
from pydoll.commands.fetch_commands import FetchCommands
from pydoll.commands.page_commands  import PageCommands
from pydoll.constants             import RequestStage
from pydoll_extensions            import TabWrapper
from utils.disqus_extractor     import fetch_disqus_config

async def disqus_only(url: str, headless: bool = False):
    forum, identifier = await fetch_disqus_config(url, headless=headless)

    options = ChromiumOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')

    async with Chrome(options=options) as browser:
        tab = TabWrapper(await browser.start())

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

            if rtype == "Document" and rurl == url:
                html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Comments</title></head>
<body>
  <div id="disqus_thread"></div>
  <script>
    var disqus_config = function () {{
      this.page.url        = '{url}';
      this.page.identifier = '{identifier}';
      this.page.title      = document.title;
    }};
  </script>
  <script src="https://{forum}.disqus.com/embed.js"
          data-timestamp="{{timestamp}}"></script>
  <noscript>Please enable JavaScript to view comments.</noscript>
</body></html>
"""
                html = html.replace("{timestamp}", str(int(time.time())))
                b64  = base64.b64encode(html.encode()).decode()
                return await tab._execute_command(
                    FetchCommands.fulfill_request(
                        request_id    = rid,
                        response_code = 200,
                        response_headers=[{"name":"Content-Type","value":"text/html"}],
                        body          = b64,
                    )
                )

            await tab._execute_command(FetchCommands.continue_request(rid))

        await tab.on("Fetch.requestPaused", on_paused)
        await tab._execute_command(PageCommands.navigate(url))
        await tab._wait_page_load()

        print("Bare Disqus page loaded. Ctrl+C to exit.")
        await asyncio.Event().wait()
