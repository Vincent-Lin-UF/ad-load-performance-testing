from pydoll.browser.options import ChromiumOptions

async def make_chrome_options(headless: bool) -> ChromiumOptions:
    options = ChromiumOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    return options