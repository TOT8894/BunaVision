"""Standalone asyncio runtime probe; run with `timeout 5s python tests/runtime_probe.py`."""

from __future__ import annotations

import asyncio
import argparse
import platform
import sys
import threading
import time


async def main(case: str) -> None:
    loop = asyncio.get_running_loop()
    print(f"python: {sys.version.replace(chr(10), ' ')}", flush=True)
    print(f"platform: {platform.platform()}", flush=True)
    print(f"loop: {type(loop).__module__}.{type(loop).__qualname__}", flush=True)
    print(
        "policy: "
        f"{type(asyncio.get_event_loop_policy()).__module__}."
        f"{type(asyncio.get_event_loop_policy()).__qualname__}",
        flush=True,
    )

    started = time.monotonic()
    if case == "to-thread":
        try:
            await asyncio.wait_for(asyncio.to_thread(time.sleep, 0.1), timeout=2)
        except TimeoutError as error:
            print(f"to_thread: TIMEOUT {error!r}", flush=True)
        else:
            print(f"to_thread: PASS elapsed={time.monotonic() - started:.6f}s", flush=True)
        return

    event = asyncio.Event()

    def notify_loop() -> None:
        loop.call_soon_threadsafe(event.set)

    try:
        worker = threading.Thread(target=notify_loop)
        worker.start()
        await asyncio.wait_for(event.wait(), timeout=2)
        worker.join(timeout=1)
    except TimeoutError as error:
        print(f"call_soon_threadsafe: TIMEOUT {error!r}", flush=True)
    else:
        print(
            f"call_soon_threadsafe: PASS elapsed={time.monotonic() - started:.6f}s",
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=("to-thread", "call-soon-threadsafe"))
    asyncio.run(main(parser.parse_args().case))
