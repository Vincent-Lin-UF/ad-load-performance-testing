# Python Imports
import asyncio
import argparse
import time
import signal
import sys
import select
import json

# PyDoll imports
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll_extensions import TabWrapper

# Local Imports
from utils.script_loader import load_script

# TTD
# Python Logging of Stats
# MORE CLI Arguments

async def runner(url):
    options = ChromiumOptions()
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
    res = await tab._execute_command({
        "method": "Runtime.evaluate",
        "params": {
            "expression": "window.getPrebidPerformanceSummary()",
            "returnByValue": True,
            "awaitPromise": True
        }
    })
    summary = res["result"]["result"]["value"]

    print(json.dumps(summary, indent=2))
    await asyncio.Event().wait()

    print("Webpage loaded and scripts executed successfully.")
        
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    
    try:
        asyncio.run(runner(args.url))
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down…")
    
if __name__ == "__main__":
    main()
        
        
        
        