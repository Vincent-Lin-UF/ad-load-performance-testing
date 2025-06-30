import asyncio
import argparse
import json
import os
import select
import sys
import time

from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.commands.page_commands import PageCommands

async def load_webpage(url: str, timeout: int):
    # Load JavaScript snippets
    with open("prebid_tracking.js", "r") as f:
        prebid_js = f.read()
    with open("performance_metrics.js", "r") as f:
        perf_js = f.read()

    # Configure Chrome options
    options = ChromiumOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    print(f"🌐 Loading webpage: {url}")
    print(f"⏱️ Timeout set to {timeout} seconds")
    print("💡 Press 'q' + Enter to quit early, or wait for timeout")
    start_time = time.perf_counter()

    async with Chrome(options=options) as browser:
        tab = await browser.start()

        # Inject Prebid tracker BEFORE navigation (critical for ad event capture)
        print("🔧 Injecting Prebid tracker before navigation...")
        await browser._execute_command(
            PageCommands.add_script_to_evaluate_on_new_document(
                source=prebid_js,
                run_immediately=False
            )
        )
        print("✅ Prebid tracker will be present from the start of every frame.")

        # Enable console logging for main tab
        await tab.enable_runtime_events()
        async def on_console(evt):
            try:
                args = evt.get("params", {}).get("args", [])
                parts = []
                for arg in args:
                    if "value" in arg:
                        parts.append(str(arg["value"]))
                    elif "preview" in arg:
                        parts.append(str(arg["preview"].get("description", "")))
                text = " ".join(parts)
                if text and not text.startswith("Blocked script execution"):
                    print(f"PAGE ▶ {text}")
            except Exception as e:
                print(f"Console log error: {e}")
        await tab.on("Runtime.consoleAPICalled", on_console)

        # Navigate to URL
        print("▶ Navigating to URL...")
        try:
            await tab.go_to(url, timeout=8)  # Only wait 8 seconds for navigation
            print("✅ Page navigation (commit) complete or timeout not reached")
        except Exception as e:
            print(f"⚠️ Navigation timed out or failed: {e}")
            print("Continuing to ad/Prebid monitoring regardless of full page load.")

        # Wait for page to stabilize
        await asyncio.sleep(2)

        # (Optional) Inject into iframes after load, in case of late iframes
        print("⏳ Looking for iframes...")
        try:
            # Use a very short timeout to avoid hanging
            iframes_result = await asyncio.wait_for(
                tab.find("iframe", find_all=True, timeout=500), 
                timeout=1.0  # 1 second max for the entire iframe search
            )
            iframes = iframes_result if isinstance(iframes_result, list) else []
            print(f"Found {len(iframes)} iframes")
            
            for i, iframe in enumerate(iframes):
                try:
                    frame_tab = await tab.get_frame(iframe)
                    # Attach console handler to iframe
                    await frame_tab.enable_runtime_events()
                    await frame_tab.on("Runtime.consoleAPICalled", on_console)
                    # Shorter wait for frame load
                    await asyncio.sleep(0.1)
                    frame_url = await frame_tab.current_url
                    if frame_url and frame_url != "about:blank":
                        # (Optional) Re-inject in case of late frame
                        await frame_tab.execute_script(prebid_js)
                        frame_name = await frame_tab.execute_script("return window.name || '<anonymous>'")
                        print(f"✅ Injected into frame {i+1}: {frame_name} @ {frame_url}")
                except Exception as e:
                    print(f"⚠️ Could not inject into iframe {i+1}: {e}")
        except asyncio.TimeoutError:
            print("⚠️ Iframe search timed out, continuing without iframe injection...")
        except Exception as e:
            print(f"⚠️ Error finding iframes: {e}")
            print("Continuing without iframe injection...")

        # Monitor for user input
        print("\n🍿 Collection running—press 'q'+Enter to finish and gather summaries.")
        print("Press 'q' + Enter to quit, or just Enter to continue monitoring...")
        
        start_monitoring = time.perf_counter()
        while True:
            # Check timeout
            elapsed = time.perf_counter() - start_monitoring
            if elapsed >= timeout:
                print(f"\n⏰ Timeout reached ({timeout} seconds). Collecting final data...")
                break
                
            # Check if there's input available (non-blocking)
            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline().strip()
                if line.lower() == "q":
                    print("Quitting monitor loop.")
                    break
                elif line == "":
                    continue
            else:
                # Give the browser time to process events
                await asyncio.sleep(0.1)
                
            # Show remaining time every 30 seconds
            if int(elapsed) % 30 == 0 and elapsed > 0:
                remaining = timeout - elapsed
                print(f"⏱️ {remaining:.0f} seconds remaining...")

        # Collect performance metrics
        print("\n📊 Collecting Core Performance Metrics:")
        try:
            perf_result = await tab.execute_script(perf_js)
            if isinstance(perf_result, dict) and 'result' in perf_result:
                result_value = perf_result.get('result', {}).get('result', {}).get('value')
                if result_value:
                    core_metrics = json.loads(result_value)
                else:
                    core_metrics = perf_result
            else:
                core_metrics = perf_result
            print("Core Performance Metrics:")
            print(json.dumps(core_metrics, indent=2))
        except Exception as e:
            print(f"⚠️ Error collecting performance metrics: {e}")

        # Collect Prebid data from main page
        print("\n🧩 Collecting Prebid Performance Data:")
        try:
            prebid_result = await tab.execute_script(
                "return window.getPrebidPerformanceSummary ? window.getPrebidPerformanceSummary() : null"
            )
            if isinstance(prebid_result, dict) and 'result' in prebid_result:
                result_value = prebid_result.get('result', {}).get('result', {}).get('value')
                if result_value:
                    prebid_data = json.loads(result_value)
                else:
                    prebid_data = prebid_result
            else:
                prebid_data = prebid_result
            if prebid_data:
                print("Prebid Performance Data (Main Page):")
                print(json.dumps(prebid_data, indent=2))
            else:
                print("No Prebid data found on main page")
        except Exception as e:
            print(f"⚠️ Error collecting Prebid data: {e}")

        # Try to collect from iframes
        print("\n🔍 Checking iframes for Prebid data...")
        try:
            # Use very short timeout for iframe search during data collection
            iframes_result = await asyncio.wait_for(
                tab.find("iframe", find_all=True, timeout=300), 
                timeout=0.5  # 0.5 seconds max for the entire iframe search
            )
            iframes = iframes_result if isinstance(iframes_result, list) else []
            print(f"Found {len(iframes)} iframes to check for Prebid data")
            
            for i, iframe in enumerate(iframes):
                try:
                    frame_tab = await tab.get_frame(iframe)
                    frame_url = await frame_tab.current_url
                    if frame_url and frame_url != "about:blank":
                        frame_prebid = await frame_tab.execute_script(
                            "return window.getPrebidPerformanceSummary ? window.getPrebidPerformanceSummary() : null"
                        )
                        if frame_prebid:
                            if isinstance(frame_prebid, dict) and 'result' in frame_prebid:
                                result_value = frame_prebid.get('result', {}).get('result', {}).get('value')
                                if result_value:
                                    frame_data = json.loads(result_value)
                                else:
                                    frame_data = frame_prebid
                            else:
                                frame_data = frame_prebid
                            frame_name = await frame_tab.execute_script("return window.name || '<anonymous>'")
                            print(f"Prebid Data (Frame {i+1}: {frame_name}):")
                            print(json.dumps(frame_data, indent=2))
                except Exception as e:
                    print(f"⚠️ Error checking iframe {i+1}: {e}")
        except asyncio.TimeoutError:
            print("⚠️ Iframe search timed out, continuing without iframe data collection...")
        except Exception as e:
            print(f"⚠️ Error checking iframes: {e}")
            print("Continuing without iframe data collection...")

        # Take screenshot
        screenshot_path = os.path.join(os.getcwd(), "prebid_summary.png")
        await tab.take_screenshot(path=screenshot_path)
        print(f"\n📸 Screenshot saved: {screenshot_path}")

        end_time = time.perf_counter()
        print(f"\n⏱️ Total execution time: {end_time - start_time:.2f} seconds")

def main():
    parser = argparse.ArgumentParser(description="Pydoll multi-frame Prebid tracking")
    parser.add_argument("url", help="URL to load and monitor")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds (default: 300)")
    args = parser.parse_args()
    
    print(f"🌐 Loading webpage: {args.url}")
    print(f"⏱️ Timeout set to {args.timeout} seconds")
    print("💡 Press 'q' + Enter to quit early, or wait for timeout")
    
    try:
        asyncio.run(load_webpage(args.url, timeout=args.timeout))
    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Done.")

if __name__ == "__main__":
    main()
