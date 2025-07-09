# Default Libraries
import base64
import asyncio
import json

# Pydoll Imports
from pydoll.commands.fetch_commands import FetchCommands
from pydoll.constants import RequestStage
from pydoll.commands.runtime_commands import RuntimeCommands

# Local Imports
from ad_load.pydoll_extensions import TabWrapper
from ad_load.loaders.template_loader import render_template
from ad_load.loaders.script_loader import load_script
from ad_load.utils.disqus_extractor import extract_disqus_info
from ad_load.utils.cdp_injector import inject_scripts
from ad_load.utils.export_prebid import export_prebid

async def disqus_only(browser, url: str, headless: bool = False, timeout: int = 30):
    extract_tab = TabWrapper(await browser.start())
    forum, identifier = await extract_disqus_info(extract_tab, url)
    await extract_tab.close()
    
    tab = TabWrapper(await browser.new_tab())
    
    # Listening for context
    contexts = {}
    await tab._execute_command(RuntimeCommands.enable())
    
    async def on_ctx(ev):
        info = ev["params"]["context"]
        aux = info.get("auxData", {})
        fId = aux.get("frameId")
        if fId:
            contexts[fId] = info["id"]
    await tab.on("Runtime.executionContextCreated",on_ctx)
    
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
    try:
        await asyncio.wait_for(asyncio.Event().wait(), timeout=30)
    except asyncio.TimeoutError:
        print("Time limit reached, exiting Disqus-only mode.")
    
    contexts_snapshot = dict(contexts)
    raw_summaries = {}
    for frame_id, ctx_id in contexts_snapshot.items():
        try:
            resp = await tab._execute_command(
                RuntimeCommands.evaluate(
                    expression="""
                        window.getPrebidPerformanceSummary
                        ? window.getPrebidPerformanceSummary()
                        : null
                    """,
                    return_by_value=True,
                    context_id=ctx_id
                )
            )
            raw_summaries[frame_id] = resp["result"]["result"]["value"]
        except Exception as e:
            raw_summaries[frame_id] = {"Error" : str(e)}
    
    filtered_summaries = {}
    for frame_id, data in raw_summaries.items():
        if not isinstance(data, dict) or "frameName" not in data:
            continue
        fname = data["frameName"]
        if fname.startswith("dsq-"):
            filtered_summaries[fname] = data
    
    out_path = "prebid_summaries.json"
    with open(out_path, "w") as f:
        json.dump(filtered_summaries, f, indent=2)
    print(f"\nWrote all frames Prebid Summaries to {out_path}")
