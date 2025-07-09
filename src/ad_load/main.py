#Default Libraries
import argparse
import asyncio

# Pydoll Imports
from pydoll.browser.chromium import Chrome

#Local Imports
from ad_load.modes.disqus_only import disqus_only
from ad_load.modes.full_page   import full_page
from ad_load.loaders.site_loader import load_site
from ad_load.utils.make_chrome_options import make_chrome_options

def build_parser() -> argparse.ArgumentParser:
    p   = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run full workflow or, with --bare, Disqus-only")
    run.add_argument("target", help="site key or URL")
    run.add_argument("--bare",    action="store_true", help="render a bare Disqus-only page")
    run.add_argument("--headless", action="store_true", help="run Chrome headless")
    run.add_argument("--mobile", action="store_true", help="Emulates a mobile device")
    run.add_argument("--timeout", type=int, default=30, help="Time before automatic exit (seconds)")
    
    sub.add_parser("list", help="show saved site shortcuts")

    return p

async def app(args):
    sites = load_site()

    if args.cmd == "list":
        for name, info in sites.items():
            print(f"{name:20} {info['url']}")
        return

    url = sites.get(args.target, {}).get("url", args.target)
    options = await make_chrome_options(
        headless=args.headless,
        mobile=args.mobile,
    )
    
    try:
        async with Chrome(options=options) as browser:
            if args.bare:
                await disqus_only(browser, url, headless=args.headless, timeout=args.timeout)
                print("Hello")
            else:
                await full_page(browser, url, headless=args.headless)
    except asyncio.CancelledError:
        pass
    except (OSError, ConnectionResetError):
        print("Chrome disconnected, exiting.")
    
    print("This is the end")
            
def main():
    args = build_parser().parse_args()
    asyncio.run(app(args))

if __name__ == "__main__":
    main()
