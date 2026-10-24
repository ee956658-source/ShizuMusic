import asyncio
import runpy

# Python 3.14 me loop apne aap nahi banta, isliye pehle hi bana do
asyncio.set_event_loop(asyncio.new_event_loop())

runpy.run_module("ShizuMusic", run_name="__main__", alter_sys=True)
