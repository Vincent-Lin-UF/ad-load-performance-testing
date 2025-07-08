# Default Libraries
import base64
import asyncio

# Pydoll Imports
from pydoll.commands.fetch_commands import FetchCommands
from pydoll.constants             import RequestStage
from pydoll.commands.page_commands import PageCommands
from pydoll.protocol.page.events import PageEvent

# Local Imports
from ad_load.pydoll_extensions            import TabWrapper
from ad_load.loaders.template_loader       import render_template
from ad_load.loaders.script_loader          import load_script
from ad_load.utils.disqus_extractor       import extract_disqus_info
from ad_load.utils.cdp_injector             import inject_scripts

async def disqus_only(browser, url: str, headless: bool = False):
    extract_tab = TabWrapper(await browser.start())
    forum, identifier = await extract_disqus_info(extract_tab, url)
    await extract_tab.close()
    
    tab = TabWrapper(await browser.new_tab())
    
    # Script Injection
    prebid_js = load_script("prebid_tracking.js")
    await inject_scripts(tab, prebid_js)

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
    
    await tab.go_to_commit(url)

    print("Bare Disqus page loaded. Ctrl+C to exit.")
    await asyncio.Event().wait()