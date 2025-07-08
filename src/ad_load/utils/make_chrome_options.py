from pydoll.browser.options import ChromiumOptions

async def make_chrome_options(headless: bool, mobile: bool = False) -> ChromiumOptions:
    options = ChromiumOptions()
    if headless:
        options.add_argument("--headless=new")
        
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    
    if mobile:
        # Emulates an iPhone
        options.add_argument(
            "--user-agent="
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        )
        
        options.add_argument("--window-size=375,812")
        options.add_argument("--force-device-scale-factor=3")
        options.add_argument("--enable-touch-events")
    return options