import time
import base64
import asyncio

from pydoll.browser.chromium      import Chrome
from pydoll.browser.options       import ChromiumOptions
from pydoll.commands.fetch_commands import FetchCommands
from pydoll.commands.page_commands  import PageCommands
from pydoll.constants             import RequestStage

from pydoll_extensions            import TabWrapper
from utils.script_loader          import load_script
from utils.disqus_extractor       import extract_disqus_info
from utils.injector             import inject_scripts
from utils.template_loader       import render_template

async def disqus_only(browser, url: str, headless: bool = False):
    extract_tab = TabWrapper(await browser.start())
    forum, identifier = await extract_disqus_info(extract_tab, url)
    await extract_tab.close()
    
    tab = TabWrapper(await browser.new_tab())

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
            html = render_template(
                "disqus_page.html",
                forum=forum,
                identifier=identifier,
                url=url
            )
#             html = f"""<!DOCTYPE html>
# <html><head><meta charset="utf-8"><title>Comments</title></head>
# <body>
# <div id="disqus_thread"></div>
# <script>
# var disqus_config = function () {{
#     this.page.url        = '{url}';
#     this.page.identifier = '{identifier}';
#     this.page.title      = document.title;
# }};
# </script>
# <script src="https://{forum}.disqus.com/embed.js"
#         data-timestamp="{{timestamp}}"></script>
# <noscript>Please enable JavaScript to view comments.</noscript>
# </body></html>
# """
#             html = html.replace("{timestamp}", str(int(time.time())))
            b64  = base64.b64encode(html.encode()).decode()
            print(html)
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
    
    # Script Injection
    prebid_js = load_script("prebid_tracking.js")
    await inject_scripts(tab, prebid_js)
    
    await tab.go_to_commit(url)

    print("Bare Disqus page loaded. Ctrl+C to exit.")
    await asyncio.Event().wait()
