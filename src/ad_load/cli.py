import asyncio
import signal
from . import main

def _make_shutdown_handler(loop):
    def _handler():
        for task in asyncio.all_tasks(loop):
            task.cancel()
    return _handler

def main_entry():
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT,  _make_shutdown_handler(loop))
    loop.add_signal_handler(signal.SIGTERM, _make_shutdown_handler(loop))
    
    try:
        asyncio.run(main.app(main.build_parser().parse_args()))
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()

if __name__ == "__main__":
    main_entry()
