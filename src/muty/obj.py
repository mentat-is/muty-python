"""
generic objects functions
"""
from collections import Counter
from contextlib import contextmanager, asynccontextmanager
import gc
from typing import Any
import tracemalloc
import psutil
import os
from muty.log import MutyLogger
import asyncio

BYTES_PER_KB = 1024
BYTES_PER_MB = 1024 * 1024


def _format_bytes(bytes_val: int) -> str:
    """Format bytes with units while preserving raw value"""
    mb_val = bytes_val / BYTES_PER_MB
    return f"{bytes_val:,} bytes ({mb_val:.2f} MB)"


def close_object(closeable: Any):
    """
    calls close on the given object
    :param closeable: object implementing close()
    :return:
    """
    if closeable and hasattr(closeable, "close"):
        # call close
        closeable.close()


def _format_memory_stats(
    mem_diff: int,
    peak_traced: int,
    vm_stats: Any,
    mem_end: int,
    gc_diff: dict,
    compare_stats: list
) -> list[str]:
    """Format memory statistics into log lines"""
    logger_lines = []
    logger_lines.append(f"[.] PID: {os.getpid()}")
    logger_lines.append(f"[.] Memory Usage: {_format_bytes(mem_diff)}")
    logger_lines.append(f"[.] Peak Memory: {_format_bytes(peak_traced)}")
    logger_lines.append(f"[.] System Memory: {
                        vm_stats.percent}% used ({_format_bytes(vm_stats.used)})")
    logger_lines.append(f"[.] Process Memory: {_format_bytes(mem_end)}")

    logger_lines.append("[.] Top 5 Memory Allocations:")
    for stat in compare_stats[:5]:
        logger_lines.append(f"{stat} ({_format_bytes(stat.size)})")

    if gc_diff:
        logger_lines.append("[.] Object Count Changes:")
        for k, v in sorted(gc_diff.items(), key=lambda x: x[1], reverse=True)[:5]:
            logger_lines.append(f"  {k}: +{v}")

    return logger_lines


async def _gather_memory_stats_async():
    """Gather memory statistics asynchronously"""
    loop = asyncio.get_running_loop()
    process = psutil.Process(os.getpid())

    await loop.run_in_executor(None, gc.collect)
    mem_info = await loop.run_in_executor(None, lambda: process.memory_info().rss)
    gc_stats = await loop.run_in_executor(
        None,
        lambda: Counter(str(o.__class__) for o in gc.get_objects())
    )
    return mem_info, gc_stats


def _gather_memory_stats():
    """Gather memory statistics synchronously"""
    process = psutil.Process(os.getpid())
    gc.collect()
    return process.memory_info().rss, Counter(str(o.__class__) for o in gc.get_objects())


@asynccontextmanager
async def track_memory_async():
    """
    Async context manager to track memory usage and log statistics
    """
    mem_start, gc_stats_start = await _gather_memory_stats_async()
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()

    try:
        yield
    finally:
        snapshot2 = tracemalloc.take_snapshot()
        mem_end, gc_stats_end = await _gather_memory_stats_async()

        stats = _format_memory_stats(
            mem_diff=mem_end - mem_start,
            peak_traced=tracemalloc.get_traced_memory()[1],
            vm_stats=psutil.virtual_memory(),
            mem_end=mem_end,
            gc_diff={k: gc_stats_end[k] - gc_stats_start[k]
                     for k in gc_stats_end
                     if gc_stats_end[k] - gc_stats_start[k] > 0},
            compare_stats=snapshot2.compare_to(snapshot1, 'lineno')
        )

        for line in stats:
            print(line)
        tracemalloc.stop()


@contextmanager
def track_memory():
    """
    Context manager to track memory usage and log statistics        
    """
    mem_start, gc_stats_start = _gather_memory_stats()
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()

    try:
        yield
    finally:
        snapshot2 = tracemalloc.take_snapshot()
        mem_end, gc_stats_end = _gather_memory_stats()

        stats = _format_memory_stats(
            mem_diff=mem_end - mem_start,
            peak_traced=tracemalloc.get_traced_memory()[1],
            vm_stats=psutil.virtual_memory(),
            mem_end=mem_end,
            gc_diff={k: gc_stats_end[k] - gc_stats_start[k]
                     for k in gc_stats_end
                     if gc_stats_end[k] - gc_stats_start[k] > 0},
            compare_stats=snapshot2.compare_to(snapshot1, 'lineno')
        )

        for line in stats:
            print(line)
        tracemalloc.stop()
