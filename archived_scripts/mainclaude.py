import asyncio
import argparse

from pydoll.browser import Chrome
from pydoll.protocol.page.events import PageEvent

async def load_webpage(url: str):
    with open("prebid_tracking.js", "r") as f:
        prebid_js = f.read()
    
    with open("performance_metrics.js", "r") as f:
        perf_js = f.read()
    
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Use tab methods instead of direct connection handler access
        try:
            # Try to inject script BEFORE navigation using CDP if possible
            print("🔧 Attempting to inject script before navigation...")
            
            # Try to access the underlying connection to inject script before page load
            try:
                # Check if we can access the connection handler differently
                if hasattr(tab, '_target'):
                    target = tab._target
                    if hasattr(target, '_connection'):
                        conn = target._connection
                        # Try to add script to evaluate on new document
                        await conn.send("Page.addScriptToEvaluateOnNewDocument", {
                            "source": prebid_js
                        })
                        print("✅ Script injected for new documents via CDP")
                    else:
                        print("⚠️ Cannot access connection, will inject after load")
                elif hasattr(tab, '_connection'):
                    conn = tab._connection
                    await conn.send("Page.addScriptToEvaluateOnNewDocument", {
                        "source": prebid_js
                    })
                    print("✅ Script injected for new documents via CDP")
                else:
                    print("⚠️ No CDP access found, will inject after load")
            except Exception as cdp_error:
                print(f"⚠️ CDP injection failed: {cdp_error}, will inject after load")
            
            metrics = {
                "requests": [],
                "page": {},
                "prebid": None
            }
            
            # Listen for page load event
            await tab.on(PageEvent.LOAD_EVENT_FIRED,
                   lambda e: metrics["page"].__setitem__("loadEventFired", e["params"]["timestamp"]))
            
            # Navigate to the URL
            print("🌐 Starting navigation to URL...")
            await tab.go_to(url)
            print("✅ Page loaded")
            
            # Also inject after load as backup
            print("💉 Injecting tracking script after load (backup)...")
            await tab.execute_script(f"({prebid_js})()")
            print("✅ Backup script injected")
            
            # Wait for any ongoing auctions/ads to complete
            print("⏳ Monitoring ad performance (15 seconds)...")
            await asyncio.sleep(15)
            
            # Try to get prebid data from main page first
            print("📊 Collecting prebid data...")
            try:
                prebid_result = await tab.execute_script("return window.getPrebidPerformanceSummary && window.getPrebidPerformanceSummary()")
                # Extract actual value from CDP response
                if isinstance(prebid_result, dict) and 'result' in prebid_result:
                    actual_result = prebid_result.get('result', {})
                    if actual_result.get('type') == 'undefined' or actual_result.get('type') == 'null':
                        metrics["prebid"] = None
                        print("⚠️ No prebid data on main page, checking iframes...")
                        raise Exception("No prebid on main page")
                    elif actual_result.get('type') == 'object' and 'objectId' in actual_result:
                        # We have an object but need to extract its properties
                        print("✅ Found prebid object, extracting data...")
                        # Try a simpler approach to get the data
                        prebid_data = await tab.execute_script("""
                            if (window.getPrebidPerformanceSummary) {
                                const data = window.getPrebidPerformanceSummary();
                                return JSON.stringify(data);
                            }
                            return null;
                        """)
                        if prebid_data and isinstance(prebid_data, dict) and 'result' in prebid_data:
                            result_value = prebid_data['result'].get('result', {}).get('value')
                            if result_value:
                                import json
                                metrics["prebid"] = json.loads(result_value)
                                print("✅ Prebid data collected from main page")
                            else:
                                metrics["prebid"] = None
                                raise Exception("Could not extract prebid data")
                        else:
                            metrics["prebid"] = None
                            raise Exception("Could not extract prebid data")
                    else:
                        metrics["prebid"] = prebid_result
                        print("✅ Prebid data collected from main page")
                else:
                    metrics["prebid"] = prebid_result
                    if prebid_result:
                        print("✅ Prebid data collected from main page")
                    else:
                        print("⚠️ No prebid data on main page, checking iframes...")
                        raise Exception("No prebid on main page")
            except Exception as e:
                print(f"⚠️ Prebid collection issue: {e}")
                # Fallback: look for iframes
                try:
                    iframe_el = await tab.find("iframe[name^='dsq-']", timeout=2000)
                    print("✅ Found iframe!")
                    frame = await tab.get_frame(iframe_el)
                    iframe_result = await frame.execute_script("return window.getPrebidPerformanceSummary()")
                    # Handle iframe result similarly
                    if isinstance(iframe_result, dict) and 'result' in iframe_result:
                        # Extract from CDP response
                        metrics["prebid"] = iframe_result  # For now, keep raw data
                    else:
                        metrics["prebid"] = iframe_result
                    print("✅ Prebid data collected from iframe")
                except Exception as iframe_e:
                    print(f"⚠️ No iframe or prebid data: {iframe_e}")
                    metrics["prebid"] = None
            
            print("📊 Collecting performance metrics...")
            try:
                perf_result = await tab.execute_script(perf_js)
                if isinstance(perf_result, dict) and 'result' in perf_result:
                    print("⚠️ Got CDP response, extracting performance data...")
                    perf_data = await tab.execute_script("""
                        const nav = performance.getEntriesByType("navigation")[0];
                        const paints = performance.getEntriesByType("paint");
                        const result = {
                            ttfb: nav ? nav.responseStart - nav.requestStart : null,
                            domContentLoaded: nav ? nav.domContentLoadedEventEnd - nav.startTime : null,
                            loadEvent: nav ? nav.loadEventEnd - nav.startTime : null,
                            fcp: paints.find(p => p.name === "first-contentful-paint")?.startTime || null,
                            lcp: paints.filter(p => p.name === "largest-contentful-paint").pop()?.startTime || null
                        };
                        return JSON.stringify(result);
                    """)
                    
                    if isinstance(perf_data, dict) and 'result' in perf_data:
                        result_value = perf_data['result'].get('result', {}).get('value')
                        if result_value:
                            import json
                            metrics["page"]["performanceMetrics"] = json.loads(result_value)
                        else:
                            metrics["page"]["performanceMetrics"] = perf_result
                    else:
                        metrics["page"]["performanceMetrics"] = perf_result
                else:
                    metrics["page"]["performanceMetrics"] = perf_result
                print("✅ Performance metrics collected")
            except Exception as e:
                print(f"⚠️ Error collecting performance metrics: {e}")
                metrics["page"]["performanceMetrics"] = None

            print("\n=== Collected Metrics ===")
            print(metrics)
            
        except Exception as e:
            print(f"Error during page load: {e}")
            try:
                metrics = {"page": {"performanceMetrics": await tab.execute_script(perf_js)}}
                print("\n=== Basic Metrics (Error Recovery) ===")
                print(metrics)
            except:
                print("Could not retrieve any metrics")
        
        finally:
            try:
                await tab.off(PageEvent.LOAD_EVENT_FIRED)
                print("\n✅ Cleanup completed")
            except:
                pass
            
            print("🏁 Script execution finished")

def main():
    parser = argparse.ArgumentParser(
        description="Load a webpage using Pydoll"
    )
    parser.add_argument("url", help="URL to load")
    args = parser.parse_args()
    
    print(f"Loading webpage: {args.url}")
    
    try:
        asyncio.run(load_webpage(args.url))
    except KeyboardInterrupt:
        print("\n⛔ Script interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        print("👋 Exiting...")
        import sys
        sys.exit(0)
    
if __name__ == "__main__":
    main()