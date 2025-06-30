import asyncio
from pydoll.browser.tab import Tab
from pydoll.commands.page_commands import PageCommands
from pydoll.protocol.page.events import PageEvent
from pydoll.exceptions import IFrameNotFound, InvalidIFrame


class TabWrapper():
    def __init__(self, real_tab: Tab):
        self._tab = real_tab
        self._cdp_lock = asyncio.Lock()
        
    async def go_to_commit(self, url: str, init_script: str):
        await self._tab._execute_command(
            PageCommands.add_script_to_evaluate_on_new_document(
                source=init_script,
                run_immediately=True
            )
        )
        
        
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
        
    async def _safe_execute(self, coro):
        async with self._cdp_lock:
            return await coro
    
    @staticmethod
    async def _add_init_script(tab: Tab, source: str):
        await tab._execute_command(
            PageCommands.add_script_to_evaluate_on_new_document(
                source=source,
                run_immediately=True
            )
        )
        # run it right away in the current document too
        await tab.execute_script(source)
        
    
    async def inject_script_into_dsq_frame(self, frame, script: str) -> bool:
        name_attr = frame.get_attribute("name") or ""
        if not name_attr.startswith("dsq-"):
            return False 

        src_attr = frame.get_attribute("src") or frame.get_attribute("srcdoc") or ""

        # 1) the easy path – src already present → normal injection
        try:
            dsq_tab = await self._safe_execute(self._tab.get_frame(frame))
            await self._safe_execute(self._add_init_script(dsq_tab, script))
            print(f"✅ installed init‑script into dsq iframe '{name_attr}'")
            return True
        except (InvalidIFrame, IFrameNotFound):
            # frame isn’t ready yet → fall back to navigation‑based
            pass

        # 2) schedule injection right after the iframe navigates
        success = await self._inject_after_navigation(frame, script)
        if success:
            return True

        # 3) (optional) very‑early injection into the initial about:blank doc
        try:
            escaped = script.replace("`", "\\`")
            await self._tab.execute_script(
                f"argument.contentWindow && argument.contentWindow.eval(`{escaped}`)",
                frame,
            )
            print(f"⚠️  early‑injected into blank iframe '{name_attr}'")
            return True
        except Exception:
            return False
    
    async def _scan_existing_iframes(self, script: str, injected: set[str]):
        async with self._cdp_lock:
            frames = await self._tab.find(tag_name="iframe", raise_exc=False, find_all=True)
            for frame in frames or []:
                name_attr = frame.get_attribute("name") or ""
                if name_attr in injected or not name_attr.startswith("dsq-"):
                    continue
                if await self.inject_script_into_dsq_frame(frame, script):
                    injected.add(name_attr)
                
    async def _inject_after_navigation(self, outer_iframe, script: str) -> bool:
        """
        Wait until *this* <iframe> finishes its first real navigation, then
        call Tab.get_frame(..) and inject the script.  Returns True on success.
        """
        iframe_id = outer_iframe.get_attribute("id")   # stable CDP‑frame id

        if not iframe_id:                      # safety – shouldn't happen
            return False

        fut: asyncio.Future[None] = asyncio.get_event_loop().create_future()

        async def _on_navigated(event):
            frame = event["params"]["frame"]
            if frame.get("id") == iframe_id and frame.get("url"):
                fut.set_result(None)

        cb_id = await self._tab.on(
            PageEvent.FRAME_NAVIGATED, _on_navigated, temporary=True
        )

        try:
            # ── wait until the iframe receives its real URL ──
            await asyncio.wait_for(fut, timeout=5)
            dsq_tab = await self._tab.get_frame(outer_iframe)   # now legal
            await self._safe_execute(self._add_init_script(dsq_tab, script))
            print(f"✅ injected after FRAME_NAVIGATED into '{iframe_id}'")
            return True
        except (asyncio.TimeoutError, InvalidIFrame, IFrameNotFound) as err:
            print(f"⚠️  navigation wait for iframe '{iframe_id}' failed: {err}")
            return False
        finally:
            await self._tab._connection_handler.remove_callback(cb_id)
                
                
    async def inject_into_disqus_frames(self,script: str, timeout: int | None = 30, scan_interval: float = 0.1) -> list[str]:
        if not self._tab.page_events_enabled:
            await self._tab.enable_page_events()

        injected: set[str] = set()
        await self._scan_existing_iframes(script, injected)

        async def _on_frame_attached(_):
            async def _safe_scan():
                try:
                    await self._scan_existing_iframes(script, injected)
                except Exception as exc:
                    # swallow the error; log if you like
                    print(f"scan failed: {exc!r}")

            asyncio.create_task(_safe_scan())

        callback_id = await self._tab.on(PageEvent.FRAME_ATTACHED, _on_frame_attached)

        try:
            if timeout is None:
                while True:
                    await self._scan_existing_iframes(script, injected)
                    await asyncio.sleep(scan_interval)
            else:
                elapsed = 0.0
                while elapsed < timeout:
                    await self._scan_existing_iframes(script, injected) 
                    await asyncio.sleep(scan_interval)
                    elapsed += scan_interval
        finally:
            await self._tab._connection_handler.remove_callback(callback_id)
        
        return list(injected)

    
    
    def __getattr__(self, name):
        return getattr(self._tab, name)