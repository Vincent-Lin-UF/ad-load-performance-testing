import asyncio
from . import main

def main_entry():
    asyncio.run(main.app(main.build_parser().parse_args()))

if __name__ == "__main__":
    main_entry()
