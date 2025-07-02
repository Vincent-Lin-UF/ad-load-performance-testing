# Default Libraries
import asyncio
import sys
import select
import json

# Local Imports
from pydoll_extensions import TabWrapper
from loaders.script_loader import load_script
from utils.injector import inject_scripts

async def full_page(browser, url: str, *, headless: bool = False) -> None:
    tab = TabWrapper(await browser.start())
        
    print(f"Loading URL: {url}")
    
    # Script Injection
    prebid_js = load_script("prebid_tracking.js")
    await inject_scripts(tab, prebid_js)
    
    await tab.go_to_commit(url)
    
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
    summary = await tab.evaluate("window.getPrebidPerformanceSummary()")

    print(json.dumps(summary, indent=2))
    await asyncio.Event().wait()

    print("Webpage loaded and scripts executed successfully.")

