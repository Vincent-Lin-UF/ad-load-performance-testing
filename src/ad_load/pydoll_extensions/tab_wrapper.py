# Default Libraries
import asyncio
import itertools
import json

# Pydoll Imports
from pydoll.browser.tab import Tab
from pydoll.commands.page_commands import PageCommands
from pydoll.protocol.page.events import PageEvent
from pydoll.commands.runtime_commands import RuntimeCommands
from pydoll.commands.dom_commands  import DomCommands


class TabWrapper():
    def __init__(self, real_tab: Tab):
        self._tab = real_tab
        self._cdp_id = itertools.count(1)
                
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
        
    async def inject_into_new_frames(self, user_script: str):
        wrapper = f"""
        (function(){{
          const fe = window.frameElement;
          console.log("[DSQ‑DBG] in frame:", fe && fe.id);
          if (!(fe && fe.id.startsWith("dsq-"))) return;
          {user_script}
        }})();
        """

        # enable DOM domain
        await self._tab._execute_command(DomCommands.enable())

        # auto‑attach for cross‑origin iframes
        await self._tab._execute_command({
            "method": "Target.setAutoAttach",
            "params": {
                "autoAttach": True,
                "waitForDebuggerOnStart": False,
                "flatten": True
            }
        })

        #  global hook for main session (top + same‑origin frames)
        await self._tab._execute_command(
            PageCommands.add_script_to_evaluate_on_new_document(
                source=wrapper,
                run_immediately=True
            )
        )

        # once page finishes loading, inject into every existing dsq-* iframe
        async def on_load(_event):
            # get the up‑to‑date frame tree
            resp_tree = await self._tab._execute_command({"method":"Page.getFrameTree"})
            if "result" not in resp_tree:
                print("[WARN] Page.getFrameTree failed:", resp_tree)
                return

            def walk(node):
                yield node["frame"]["id"]
                for child in node.get("childFrames", []):
                    yield from walk(child)

            for frame_id in walk(resp_tree["result"]["frameTree"]):
                # find the <iframe> owning this frame
                resp_owner = await self._tab._execute_command(
                    DomCommands.get_frame_owner(frame_id=frame_id)
                )
                if "result" not in resp_owner:
                    continue
                backend = resp_owner["result"]["backendNodeId"]

                # read its attributes
                resp_attrs = await self._tab._execute_command(
                    DomCommands.get_attributes(node_id=backend)
                )
                if "result" not in resp_attrs:
                    continue

                attr_list = resp_attrs["result"]["attributes"]
                # build dict
                attrs = dict(zip(attr_list[0::2], attr_list[1::2]))
                dsq_id = attrs.get("id", "")
                if dsq_id.startswith("dsq-"):
                    await self._tab._execute_command(
                        PageCommands.add_script_to_evaluate_on_new_document(
                            source=wrapper,
                            run_immediately=True,
                            frameId=frame_id
                        )
                    )
                    print(f"[INFO] injected into existing DSQ frame {dsq_id}")

        # one‑time listener on load
        await self._tab.on(PageEvent.LOAD_EVENT_FIRED, on_load, temporary=True)

        # 5) catch any new cross‑origin iframes
        async def on_attach(evt):
            info      = evt["params"]["targetInfo"]
            sessionId = evt["params"]["sessionId"]
            if info.get("type") != "iframe":
                return

            ws = self._tab._connection_handler._ws_connection
            msg = {
                "id": next(self._cdp_id),
                "method": "Page.addScriptToEvaluateOnNewDocument",
                "params": {"source": wrapper, "runImmediately": True},
                "sessionId": sessionId
            }
            await ws.send(json.dumps(msg))
            print(f"[INFO] injected into new cross‑origin DSQ iframe {info['targetId']}")

        await self._tab.on("Target.attachedToTarget", on_attach)

        print("[INFO] master DSQ injector registered")
        
        
    def __getattr__(self, name):
        return getattr(self._tab, name)