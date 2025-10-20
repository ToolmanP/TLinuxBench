#!/usr/bin/python

import asyncio
import json
import os
import select
import sys
import time
from ctypes import c_uint8, c_uint32

from bcc import BPF
from qemu.qmp import QMPClient

from utils import get_logger

logger = get_logger()

ptext = """
#include <linux/sched.h>
BPF_HASH(target_pids, u32, u8);
BPF_HASH(sched_count, u64, u64);
BPF_HASH(last_scheduled_cpu, u32, u32);
static inline u64 make_key(u32 pid, u32 cpu) {
    return ((u64)pid << 32) | (u64)cpu;
}
TRACEPOINT_PROBE(sched, sched_switch) {
    u32 next_pid = args->next_pid;
    if (target_pids.lookup(&next_pid)) {
        u32 cpu = bpf_get_smp_processor_id();
        u64 key = make_key(next_pid, cpu);
        u64 zero = 0, *val;
        val = sched_count.lookup_or_init(&key, &zero);
        __sync_fetch_and_add(val, 1);

        for 
    }
    return 0;
}
"""


async def main(qemu_pid: str):
    qmp = QMPClient("trace_vcpu_sched")

    logger.info(f"waiting qemu_pid:{qemu_pid}")
    while not os.path.exists(f"/tmp/{qemu_pid}.socket"):
        logger.info("waiting")
        time.sleep(1)

    await qmp.connect(f"/tmp/{qemu_pid}.socket")
    with qmp.listener(names="ACPI_DEVICE_OST") as listener:
        await qmp.execute("cont")
        await listener.get()
        await qmp.execute("stop")

    info = await qmp.execute("query-cpus-fast")
    logger.info(info)
    thread_map = {}
    for cpu_info in info:
        thread_map[cpu_info["thread-id"]] = cpu_info["props"]["core-id"]

    bpf = BPF(text=ptext)
    target_map = bpf["target_pids"]

    for pid in thread_map.keys():
        target_map[c_uint32(pid)] = c_uint8(1)

    count_map = bpf["sched_count"]

    result = {}
    for pid, cpu in thread_map.items():
        logger.info(f"Received vcpu: {cpu} pid: {pid}")
        result[pid] = {"vcpu": cpu, "scheds": {}}

    file = f"/tmp/trace_vcpu_sched-{qemu_pid}-{time.time()}.json"
    logger.info(f"Logging vcpu scheduling to {file}")

    await qmp.execute("cont")
    await qmp.disconnect()

    pidfd = os.pidfd_open(int(qemu_pid), 0)
    select.select([pidfd], [], [])

    for key, count in count_map.items():
        key_val = int.from_bytes(key, "little")
        pid = key_val >> 32
        cpu = key_val & 0xFFFFFFFF
        count_val = int.from_bytes(count, "little")
        result[pid]["scheds"][cpu] = count_val

    with open(file, "w") as f:
        json.dump(result, f, indent=2)


if len(sys.argv) != 2:
    sys.exit(1)

logger.info("helflo")
asyncio.run(main(qemu_pid=sys.argv[1]))
