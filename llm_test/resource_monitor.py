import os
import csv
import psutil
import pandas as pd
import asyncio
import signal

_cpu_cols = ['timestamp', 'load_1m', 'load_5m', 'load_15m', 'cpu', 'mem', 'swap']
_gpu_cols = ['timestamp', 'gpu_id', 'gpu', 'gpu_mem', 'gpu_mem_used', 'gpu_mem_total', 'pci']
_bgn_time = pd.Timestamp.now()
_terminal = 0

df_cpu = pd.DataFrame(columns=_cpu_cols)
df_gpu = pd.DataFrame(columns=_gpu_cols)

def signal_handler(sig, frame):
    _terminal = 1

async def resource_monitor():
    while not _terminal:
        t = (pd.Timestamp.now() - _bgn_time).total_seconds()
        # 获取系统负载情况
        load = psutil.getloadavg()
        # 获取CPU使用率
        # cpu = psutil.cpu_percent(interval=1, percpu=True)
        cpu = psutil.cpu_percent(interval=None)
        # 获取内存使用情况
        mem = psutil.virtual_memory() 
        # 获取交换空间使用情况
        swap = psutil.swap_memory()
        # 获取GPU使用情况（所有显卡）
        # gpu_info = os.popen('nvidia-smi --query-gpu=index,utilization.gpu,utilization.memory,memory.used,memory.total,pci --format=csv')
        gpu_info = os.popen('nvidia-smi --query-gpu=index,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv')
        gpu_info = list(csv.reader(gpu_info))
        # 获取所有显卡的使用情况
        # gpu_mem = [int(i[1].strip().split()[0]) for i in gpu_info[1:]]
        df_tmp = pd.DataFrame(gpu_info[1:], _gpu_cols[1:])
        df_tmp['timestamp'] = t
        df_gpu = df_gpu.append(df_tmp)
        print(f"记录系统开销于第{t}秒")
        asyncio.sleep(2)

signal.signal(signal.SIGTERM, signal_handler)

asyncio.run(resource_monitor())

print(df_cpu)
print(df_gpu)
