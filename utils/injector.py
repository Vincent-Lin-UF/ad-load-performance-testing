from pydoll_extensions import TabWrapper

async def inject_scripts(tab: TabWrapper, *scripts: str) -> None:
    for script in scripts:
        await tab.inject_script(script)
        await tab.inject_into_new_frames(script)