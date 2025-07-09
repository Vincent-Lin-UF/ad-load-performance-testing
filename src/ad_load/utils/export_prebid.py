import asyncio

from pydoll.commands.runtime_commands import RuntimeCommands

async def export_prebid(tab, timeout=1):
    
    await tab._execute_command(RuntimeCommands.enable())
    
    contexts = {}
    
    async def on_ctx(ev):
        info = ev["params"]["context"]
        aux = info.get("auxData", {})
        fId = aux.get("frameId")
        if fId:
            contexts[fId] = info["id"]
            
    await tab.on("Runtime.executionContextCreated", on_ctx)
    
    await asyncio.sleep(timeout)
    
    results = {}
    for frame_id, ctx_id in contexts.items():
        try:
            resp = await tab._execute_command(
                RuntimeCommands.evaluate(
                    expression="""
                        (window.getPrebidPerformanceSummary
                        ? window.getPrebidPerformanceSummary()
                        : null)
                    """,
                    return_by_value=True,
                    context_id=ctx_id
                )
            )
            results[frame_id] = resp["result"]["result"]["value"]
        except Exception as e:
            results[frame_id] = {"Error": str(e)}
    
    print(results)