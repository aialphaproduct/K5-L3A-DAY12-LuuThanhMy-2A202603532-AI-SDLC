"""Ticket-04 soak test and cross-platform memory helpers (no third-party deps)."""
import json
import os
import platform
import random
import sys
import time

from simulation import DURATIONS, Game


def rss_mb():
    """Current resident set size of this process in MB (Windows, Linux, macOS)."""
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD),
                        ('PeakWorkingSetSize', ctypes.c_size_t), ('WorkingSetSize', ctypes.c_size_t),
                        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t), ('QuotaPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t), ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                        ('PagefileUsage', ctypes.c_size_t), ('PeakPagefileUsage', ctypes.c_size_t)]
        pmc = PMC(); pmc.cb = ctypes.sizeof(PMC)
        k32 = ctypes.WinDLL('kernel32'); psapi = ctypes.WinDLL('psapi')
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
        psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
        return pmc.WorkingSetSize / 2**20
    if os.path.exists('/proc/self/status'):
        with open('/proc/self/status') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return int(line.split()[1]) / 1024
    import subprocess  # macOS: ps reports current RSS in KB
    out = subprocess.run(['ps', '-o', 'rss=', '-p', str(os.getpid())], capture_output=True, text=True).stdout
    return int(out.strip() or 0) / 1024


def os_label():
    return f'{platform.system()} {platform.release()} ({platform.machine()}), Python {platform.python_version()}'


def soak(seed=7, nights=10, out='soak.json'):
    """Run `nights` headless nights back to back in one process with seeded random input."""
    t0 = time.perf_counter()
    results, crashes, mem_start, mem_end = [], 0, None, None
    for i in range(nights):
        night = i % 3 + 1
        nseed = seed + i
        try:
            g = Game(nseed, night)
            if mem_start is None:
                mem_start = rss_mb()  # after the first night has loaded
            rng = random.Random(nseed)
            move = [0.0, 0.0]
            for k in range(DURATIONS[night] * 60):
                if k % 30 == 0:
                    move = [rng.uniform(-1, 1), rng.uniform(-1, 1)]
                g.input.update({'move': move, 'jump': rng.random() < .05, 'dash': rng.random() < .03,
                                'pulse': rng.random() < .02, 'interact': rng.random() < .10})
                g.step()
                g.events.clear()
                if g.state in ('won', 'lost'):
                    break
            results.append(g.state if g.state in ('won', 'lost') else 'lost')
        except Exception as exc:  # a crash is counted, the soak keeps going
            crashes += 1
            results.append('crash')
            print(f'night {i + 1} crashed: {exc!r}', file=sys.stderr)
        g = None  # reset before the next night
    mem_end = rss_mb()  # after the last night has been reset
    report = {'nights': nights, 'crashes': crashes, 'results': results,
              'mem_start_mb': round(mem_start or 0, 1), 'mem_end_mb': round(mem_end, 1),
              'duration_s': round(time.perf_counter() - t0, 1)}
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    return report
