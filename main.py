#!/usr/bin/env python3
import argparse, asyncio
from modes.disqus_only import disqus_only
from modes.full_page   import full_page
from utils.site_loader import load_site

def build_parser() -> argparse.ArgumentParser:
    p   = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run full workflow or, with --bare, Disqus-only")
    run.add_argument("target", help="site key or URL")
    run.add_argument("--bare",    action="store_true", help="render a bare Disqus-only page")
    run.add_argument("--headless", action="store_true", help="run Chrome headless")
    
    sub.add_parser("list", help="show saved site shortcuts")

    return p

def main():
    args  = build_parser().parse_args()
    sites = load_site()

    if args.cmd == "list":
        for name, info in sites.items():
            print(f"{name:20} {info['url']}")
        return

    url = sites.get(args.target, {}).get("url", args.target)
    headless = args.headless

    if args.bare:
        runner = disqus_only
    else:
        runner = full_page

    try:
        asyncio.run(runner(url, headless=headless))
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down…")


if __name__ == "__main__":
    main()
