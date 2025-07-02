# Default Libraries
import asyncio

# Pydoll Imports
from pydoll.browser.tab import Tab
from pydoll.commands.page_commands import PageCommands
from pydoll.protocol.page.events import PageEvent
from pydoll.commands.runtime_commands import RuntimeCommands

class TabWrapper():
    def __init__(self, real_tab: Tab):
        self._tab = real_tab
                
    async def go_to_commit(self, url: str):
        if await self._tab._refresh_if_url_not_changed(url):
            return

        if not self._tab.page_events_enabled:
            await self._tab.enable_page_events()

        await self._tab._execute_command(PageCommands.navigate(url))

        fut = asyncio.get_event_loop().create_future()
        async def on_frame_navigated(event):
            if event["params"]["frame"].get("url") == url:
                fut.set_result(None)
        await self._tab.on(PageEvent.FRAME_NAVIGATED, on_frame_navigated, temporary=True)
        await fut
        
    async def evaluate(self, expression: str):
        resp = await self._tab._execute_command(
            RuntimeCommands.evaluate(
                expression=expression,
                return_by_value=True
            )
        )
        print(resp)
        return resp["result"]["result"]["value"]
    
    async def inject_script(self, script: str):
        await self._tab._execute_command(
            PageCommands.add_script_to_evaluate_on_new_document(
                source=script,
                run_immediately=True
            )
        )
        
    async def inject_into_new_frames(self, script: str):
        async def _on_attached(event):
            frame_id = event["params"]["frameId"]
            try:
                child = await self._tab.frame(frame_id)  
                await child._execute_command(  
                    PageCommands.add_script_to_evaluate_on_new_document(
                        source=script,
                        run_immediately=True,
                        frameId=frame_id
                    )
                )
            except Exception as err:
                print(f"Skip frame {frame_id[:8]}… ({err})")
        
        await self._tab.on(PageEvent.FRAME_ATTACHED, _on_attached)

    def __getattr__(self, name):
        return getattr(self._tab, name)