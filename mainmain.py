# Python Imports
import asyncio
import argparse
import sys
import select
import json

# PyDoll imports
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

# Local Imports
from pydoll_extensions import TabWrapper
from utils.script_loader import load_script
from utils.site_loader import load_site

# TTD
# Python Logging of Stats
# Fix injections in iframes. It is not doing it correctly.

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    
    run = sub.add_parser("run")
    run.add_argument("target")
    run.add_argument("--headless", action="store_true", default=False)
    
    sub.add_parser("list")
    
    return p

async def runner(url: str, *, headless: bool = False) -> None:
    options = ChromiumOptions()
    
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    
    async with Chrome(options=options) as browser:
        await load_webpage(browser, url)

async def load_webpage(browser: Chrome, url: str):
    prebid_js  = load_script("prebid_tracking.js")
    perf_js    = load_script("performance_metrics.js")
    disqus_js  = load_script("only_disqus.js")
    
    real_tab = await browser.start()
    tab = TabWrapper(real_tab)
    
    print(f"Loading URL: {url}")
    
    await tab.go_to_commit(url, prebid_js)
    
    # for frame in tab.frames():
    #     try:
    #         await frame.inject_script(prebid_js)
    #     except Exception as e:
    #         print(f"Error injecting script into frame {frame.id}: {e}")
    
    await tab.inject_into_new_frames(prebid_js)
            
    disqus_tag = await tab.find(
        id='disqus_thread',
        timeout=10,
        raise_exc=False
    )
    
    if not disqus_tag:
        print("The site does not have Disqus Threads")
        return
    
    print("\nMonitoring for PBJS events...")
    print("Press 'q' + Enter to quit, or just Enter to continue monitoring...")
    while True:
        if sys.stdin in select.select([sys.stdin], [], [], 0.0)[0]:
            line = sys.stdin.readline().strip().lower()
            if line == "q":
                print("Quitting monitor loop.")
                break
        await asyncio.sleep(0.1)
    
    print("Gathering summary from page…")
    # res = await tab._execute_command({
    #     "method": "Runtime.evaluate",
    #     "params": {
    #         "expression": "window.getPrebidPerformanceSummary()",
    #         "returnByValue": True,
    #         "awaitPromise": True
    #     }
    # })
    # print("Here", res)
    # summary = res["result"]["result"]["value"]
    summary = await tab.evaluate("window.getPrebidPerformanceSummary()")

    print(json.dumps(summary, indent=2))
    await asyncio.Event().wait()

    print("Webpage loaded and scripts executed successfully.")
        
def main():
    args = build_parser().parse_args()
    sites = load_site()
    
    if args.cmd == "list":
        for site, link in sites.items():
            print(f"{site:20} {link['url']}")
        return
        
    url = sites.get(args.target, {}).get("url", args.target)
    
    try:
        asyncio.run(runner(url, headless=args.headless))
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down…")
    
if __name__ == "__main__":
    main()