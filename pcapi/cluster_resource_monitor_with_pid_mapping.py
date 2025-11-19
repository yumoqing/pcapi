#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import csv
from kubernetes import client, config
import pynvml
import subprocess

# ----------------------------
# 1. 初始化 Kubernetes
# ----------------------------
try:
    kubeconfig_path = os.environ.get("KUBECONFIG", "/root/.kube/config")
    config.load_kube_config(config_file=kubeconfig_path)
except Exception as e:
    print(f"Error loading kubeconfig: {e}")
    sys.exit(1)

v1 = client.CoreV1Api()
crd_api = client.CustomObjectsApi()

# ----------------------------
# 2. 初始化 NVIDIA
# ----------------------------
try:
    pynvml.nvmlInit()
    gpu_count = pynvml.nvmlDeviceGetCount()
except Exception as e:
    print(f"No NVIDIA GPU found or driver not installed: {e}")
    gpu_count = 0

# ----------------------------
# 3. 节点资源
# ----------------------------
nodes_info = []
gpu_nodes = {}
for node in v1.list_node().items:
    name = node.metadata.name
    status = next((cond.type for cond in node.status.conditions if cond.status=="True"), "Unknown")
    cpu = node.status.allocatable.get('cpu', '0')
    memory = node.status.allocatable.get('memory', '0')
    gpu = node.status.allocatable.get('nvidia.com/gpu', '0')
    nodes_info.append({'name': name,'status': status,'cpu_allocatable': cpu,'memory_allocatable': memory,'gpu_allocatable': gpu})
    if gpu != '0':
        gpu_nodes[name] = int(gpu)

# ----------------------------
# 4. Pod资源
# ----------------------------
pods_info = []
pod_pid_map = {}  # key=PID, value=(namespace,pod_name)
for pod in v1.list_pod_for_all_namespaces().items:
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace
    node_name = pod.spec.node_name
    for c in pod.spec.containers:
        cpu_req = c.resources.requests.get('cpu', '0') if c.resources.requests else '0'
        mem_req = c.resources.requests.get('memory', '0') if c.resources.requests else '0'
        gpu_req = c.resources.requests.get('nvidia.com/gpu', '0') if c.resources.requests else '0'
        pods_info.append({
            'namespace': namespace,
            'pod_name': pod_name,
            'node': node_name,
            'container': c.name,
            'cpu_request': cpu_req,
            'memory_request': mem_req,
            'gpu_request': gpu_req
        })
    # 获取容器 PID 映射 (离线环境需有 nsenter 或 crictl)
    try:
        cmd = f"crictl inspectp $(crictl ps --name {pod_name} -q)"
        out = subprocess.check_output(cmd, shell=True).decode()
        # 简化处理，只提取 PID
        import re
        pids = re.findall(r'"pid":\s*(\d+)', out)
        for pid in pids:
            pod_pid_map[int(pid)] = (namespace, pod_name)
    except Exception:
        continue

# ----------------------------
# 5. KubeVirt VM资源
# ----------------------------
vms_info = []
vm_pid_map = {}  # key=PID, value=(namespace,vm_name)
namespaces = [ns.metadata.name for ns in v1.list_namespace().items]
for ns in namespaces:
    try:
        vms = crd_api.list_namespaced_custom_object(
            group="kubevirt.io",
            version="v1",
            namespace=ns,
            plural="virtualmachines"
        )
        for vm in vms.get('items', []):
            name = vm['metadata']['name']
            spec = vm.get('spec', {}).get('template', {}).get('spec', {})
            domain = spec.get('domain', {})
            resources = domain.get('resources', {}).get('requests', {})
            cpu = resources.get('cpu', '0')
            memory = resources.get('memory', '0')
            gpus = domain.get('devices', {}).get('gpus', [])
            vms_info.append({
                'namespace': ns,
                'vm_name': name,
                'cpu_request': cpu,
                'memory_request': memory,
                'gpus': gpus
            })
            # 获取 virt-launcher Pod PID
            try:
                vl_pods = v1.list_namespaced_pod(namespace=ns, label_selector=f"kubevirt.io=virt-launcher,vm={name}")
                for vl_pod in vl_pods.items:
                    cmd = f"crictl inspectp $(crictl ps --name {vl_pod.metadata.name} -q)"
                    out = subprocess.check_output(cmd, shell=True).decode()
                    import re
                    pids = re.findall(r'"pid":\s*(\d+)', out)
                    for pid in pids:
                        vm_pid_map[int(pid)] = (ns, name)
            except Exception:
                continue
    except client.exceptions.ApiException:
        continue

# ----------------------------
# 6. GPU实时使用 + PID映射
# ----------------------------
gpu_info = []
if gpu_count > 0:
    for i in range(gpu_count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        name = pynvml.nvmlDeviceGetName(handle).decode()
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)

        processes = []
        try:
            for proc in pynvml.nvmlDeviceGetComputeRunningProcesses(handle):
                pid = proc.pid
                used_mem = proc.usedGpuMemory // 1024**2
                owner = pod_pid_map.get(pid) or vm_pid_map.get(pid) or ("unknown", "unknown")
                processes.append({
                    'pid': pid,
                    'used_memory_MB': used_mem,
                    'owner_type': 'pod' if pid in pod_pid_map else 'vm' if pid in vm_pid_map else 'unknown',
                    'namespace': owner[0],
                    'name': owner[1]
                })
        except pynvml.NVMLError:
            pass

        gpu_info.append({
            'gpu_index': i,
            'name': name,
            'memory_total_MB': mem_info.total // 1024**2,
            'memory_used_MB': mem_info.used // 1024**2,
            'gpu_util_percent': util.gpu,
            'mem_util_percent': util.memory,
            'processes': processes
        })

# ----------------------------
# 7. 输出 JSON 和 CSV
# ----------------------------
output = {'nodes': nodes_info, 'pods': pods_info, 'vms': vms_info, 'gpus': gpu_info}
with open("cluster_resources.json", "w") as f:
    json.dump(output, f, indent=2)

# CSV输出函数
def write_csv(filename, data, fieldnames):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

write_csv("nodes.csv", nodes_info, ['name','status','cpu_allocatable','memory_allocatable','gpu_allocatable'])
write_csv("pods.csv", pods_info, ['namespace','pod_name','node','container','cpu_request','memory_request','gpu_request'])
write_csv("vms.csv", vms_info, ['namespace','vm_name','cpu_request','memory_request','gpus'])
write_csv("gpus.csv", gpu_info, ['gpu_index','name','memory_total_MB','memory_used_MB','gpu_util_percent','mem_util_percent','processes'])

print("Cluster resource report generated with GPU PID → Pod/VM mapping")
print(" - cluster_resources.json")
print(" - nodes.csv, pods.csv, vms.csv, gpus.csv")

