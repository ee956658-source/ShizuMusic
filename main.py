import asyncio
import runpy

asyncio.set_event_loop(asyncio.new_event_loop())

runpy.run_module("ShizuMusic", run_name="__main__", alter_sys=True)
