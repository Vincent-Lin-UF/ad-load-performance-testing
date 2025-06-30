#!/usr/bin/env python3
import asyncio
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

async def test_basic_functionality():
    print("Testing browser automation...")
    
    options = ChromiumOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        async with Chrome(options=options) as browser:
            tab = await browser.start()
            print("Browser started successfully")
            
            await tab.go_to("https://vincent-lin.com/blog/hello-world")
            print("Navigation successful")
            
            title = await tab.execute_script("return document.title")
            print(f"Page title: {title}")
            
            print("🎉 All tests passed!")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())