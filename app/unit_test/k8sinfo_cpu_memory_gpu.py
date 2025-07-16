from kubernetes import client, config
import json
import re
from typing import Dict, Any, List, Tuple
import yaml
import time

def get_node_info(kubeconfig):
    try:
        # 加载配置
        kubeconfig = yaml.safe_load(kubeconfig)
        config.load_kube_config_from_dict(kubeconfig)
        v1 = client.CoreV1Api()
        api_client = client.ApiClient()
        
        # 获取节点指标和 Pod 列表
        node_metrics_path = "/apis/metrics.k8s.io/v1beta1/nodes"
        node_metrics_response = api_client.call_api(
            node_metrics_path, 'GET', auth_settings=['BearerToken'], response_type='object')[0]
        node_metrics = {node['metadata']['name']: node.get('usage', {})
                        for node in node_metrics_response.get('items', [])}
        
        # 获取所有 Pod 及其资源请求
        pods = v1.list_pod_for_all_namespaces().items
        node_pod_resources = {}  # 存储每个节点上 Pod 的资源请求
        print(pods)
        
        for pod in pods:
            if pod.spec.node_name and pod.status.phase in ["Running", "Pending"]:
                node_name = pod.spec.node_name
                if node_name not in node_pod_resources:
                    node_pod_resources[node_name] = {
                        "cpu": 0,
                        "memory": 0,
                        "gpu": 0
                    }
                
                # 累加容器请求的资源
                for container in pod.spec.containers:
                    if container.resources and container.resources.requests:
                        # CPU (转换为 millicores)
                        cpu_request = container.resources.requests.get("cpu", "0m")
                        cpu_millis = int(float(cpu_request.rstrip("m"))) if "m" in cpu_request else int(float(cpu_request) * 1000)
                        node_pod_resources[node_name]["cpu"] += cpu_millis
                        
                        # Memory (转换为 bytes)
                        memory_request = container.resources.requests.get("memory", "0")
                        memory_bytes = int(float(memory_request.rstrip("KiMiGi")))
                        if "Ki" in memory_request:
                            memory_bytes *= 1024
                        elif "Mi" in memory_request:
                            memory_bytes *= 1024 * 1024
                        elif "Gi" in memory_request:
                            memory_bytes *= 1024 * 1024 * 1024
                        node_pod_resources[node_name]["memory"] += memory_bytes
                        
                        # GPU
                        gpu_request = container.resources.requests.get("nvidia.com/gpu", "0")
                        node_pod_resources[node_name]["gpu"] += int(gpu_request)
        
        # 获取节点列表并计算资源使用情况
        nodes = v1.list_node().items
        rows = []
        
        for node in nodes:
            node_name = node.metadata.name
            internal_ip = next((address.address for address in node.status.addresses
                               if address.type == "InternalIP"), "未分配")
            external_ip = next((address.address for address in node.status.addresses
                               if address.type == "ExternalIP"), "未分配")
            status = node.status.conditions[-1].status if node.status.conditions else "Unknown"
            status = "已就绪" if status == "True" else "未就绪"
            
            # 节点角色
            roles = []
            role_labels = [
                "node-role.kubernetes.io/control-plane",
                "node-role.kubernetes.io/master",
                "node-role.kubernetes.io/worker"
            ]
            for label in role_labels:
                if label in node.metadata.labels:
                    roles.append(label.split("/")[-1])
            roles_str = "控制节点" if roles else "工作节点"
            
            # 节点运行时间
            running_time = time.time() - node.metadata.creation_timestamp.timestamp()
            node_age = running_time
            
            # 节点信息
            k8s_version = node.status.node_info.kubelet_version
            os_image = node.status.node_info.os_image
            kernel_version = node.status.node_info.kernel_version
            container_runtime = node.status.node_info.container_runtime_version
            
            # 自定义标签
            labels = node.metadata.labels
            kyy_labels = [f"{k}={v}" for k, v in labels.items() if k.startswith('kyy-')]
            
            # 实时资源使用情况
            cpu_usage = node_metrics.get(node_name, {}).get('cpu', 'undefined')
            if cpu_usage and isinstance(cpu_usage, str):
                cpu_usage = int(cpu_usage.replace("n", ""))
                cpu_usage = f'{(cpu_usage / 1000000 / 1000):.3f}核'
            
            memory_usage = node_metrics.get(node_name, {}).get('memory', 'undefined')
            if memory_usage and isinstance(memory_usage, str):
                memory_usage = int(memory_usage.replace("Ki", ""))
                memory_usage = f"{(memory_usage / 1024 / 1024):.3f}Gi"
            
            # 节点总资源
            total_cpu = float(node.status.allocatable.get("cpu", "0"))
            total_memory = parse_resource_value(node.status.allocatable.get("memory", "0")) / (1024 ** 1) #内存默认Mi转成Gi
            total_gpu = int(node.status.allocatable.get("nvidia.com/gpu", "0"))
            
            # 已分配资源
            allocated_cpu = node_pod_resources.get(node_name, {}).get("cpu", 0) / 1000.0  # 转换为 cores
            allocated_memory = node_pod_resources.get(node_name, {}).get("memory", 0) / (1024 ** 3)  # 转换为 Gi
            allocated_gpu = node_pod_resources.get(node_name, {}).get("gpu", 0)
            
            # 可用资源
            available_cpu = total_cpu - allocated_cpu
            available_memory = total_memory - allocated_memory
            available_gpu = total_gpu - allocated_gpu
            
            node_info = {
                # "node_name": node_name,
                # "node_status": status,
                # "node_role": roles_str,
                # "node_age": node_age,
                # "node_version": k8s_version,
                # "node_internalip": internal_ip,
                # "node_externalip": external_ip,
                # "node_osversion": os_image,
                # "node_kernelversion": kernel_version,
                # "node_containeruntime": container_runtime,
                # "node_labels": kyy_labels,
                # "node_cpurate": cpu_usage,
                # "node_memrate": memory_usage,
                # 新增资源信息
                "node_total_cpu": f"{total_cpu:.2f}核",
                "node_allocated_cpu": f"{allocated_cpu:.2f}核",
                "node_available_cpu": f"{available_cpu:.2f}核",
                "node_cpu_usage_percent": f"{(allocated_cpu / total_cpu * 100):.1f}%" if total_cpu > 0 else "0%",
                
                "node_total_memory": f"{total_memory:.2f}Gi",
                "node_allocated_memory": f"{allocated_memory:.2f}Gi",
                "node_available_memory": f"{available_memory:.2f}Gi",
                "node_memory_usage_percent": f"{(allocated_memory / total_memory * 100):.1f}%" if total_memory > 0 else "0%",
                
                "node_total_gpu": total_gpu,
                "node_allocated_gpu": allocated_gpu,
                "node_available_gpu": available_gpu,
                "node_gpu_usage_percent": f"{(allocated_gpu / total_gpu * 100):.1f}%" if total_gpu > 0 else "0%"
            }
            rows.append(node_info)
        
        result = {
            "total": len(rows),
            "rows": rows
        }
        print(f"=== node_info={result}")
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"获取节点信息失败: {e}")
        raise e

# 辅助函数：解析资源值
def parse_resource_value(value: str) -> float:
    """解析 Kubernetes 资源值（如 "1.5", "500m", "2Gi"）为统一单位"""
    if not value:
        return 0.0
    
    # 处理 CPU (cores 或 millicores)
    if value.endswith('m'):
        return float(value[:-1]) / 1000.0  # 转换为 cores
    elif re.match(r'^\d+(\.\d+)?$', value):
        return float(value)  # 已经是 cores
    
    # 处理内存 (Ki, Mi, Gi, Ti)
    elif value.endswith('Ki'):
        return float(value[:-2]) / (1024 ** 1)  # 转换为 Gi
    elif value.endswith('Mi'):
        return float(value[:-2]) / (1024 ** 2)
    elif value.endswith('Gi'):
        return float(value[:-2])
    elif value.endswith('Ti'):
        return float(value[:-2]) * 1024
    
    return float(value)  # 默认按原单位返回


def get_pod_info(kubeconfig):
    try:
        # config.load_kube_config()
        kubeconfig = yaml.safe_load(kubeconfig)
        config.load_kube_config_from_dict(kubeconfig)
        v1 = client.CoreV1Api()
        api_client = client.ApiClient()

        namespaces = v1.list_namespace().items
        non_system_namespaces = [ns.metadata.name for ns in namespaces if
                                 not ns.metadata.name.startswith(('kube-', 'default', 'local', 'ingress-'))]

        rows = []
        for namespace in non_system_namespaces:
            pods = v1.list_namespaced_pod(namespace).items
            pod_metrics_path = f"/apis/metrics.k8s.io/v1beta1/namespaces/{namespace}/pods"
            pod_metrics_response = api_client.call_api(
                pod_metrics_path, 'GET', auth_settings=['BearerToken'], response_type='object')[0]
            pod_metrics = {pod['metadata']['name']: pod.get("containers",[{}])[0].get('usage', {})
                           for pod in pod_metrics_response.get('items', [])}
            
            # debug(f"### pod_metrics_response={pod_metrics_response}")
            for pod in pods:
                pod_name = pod.metadata.name
                if pod.status.container_statuses:
                    ready_count = sum(1 for cs in pod.status.container_statuses if cs.ready)
                else:
                    ready_count = 0
                ready_status = f"{ready_count}/{len(pod.spec.containers)}"
                readiness_conditions = [{"type": cond.type, "status": cond.status}
                                        for cond in pod.status.conditions if cond.type == "Ready"]
                phase = pod.status.phase
                restart_count = sum(cs.restart_count for cs in pod.status.container_statuses) if pod.status.container_statuses else 0
                running_time = time.time() - pod.metadata.creation_timestamp.timestamp()
                pod_age = running_time
                pod_ip = pod.status.pod_ip if pod.status.pod_ip else "Unknown"
                node_name = pod.spec.node_name if pod.spec.node_name else "Pod未被调度到节点"
                nominated_node = pod.status.nominated_node_name if pod.status.nominated_node_name else "无"

                if phase == "Pending":
                    pod_ip = "Pending状态,未分配 IP"
                    node_name = "Pending状态,未分配节点"
                    nominated_node = "Pending状态,未分配节点"


                # ✅ 提取容器的资源限制（limits）
                cpu_limit = "未设置"
                memory_limit = "未设置"
                gpu_limit = "未设置"

                if pod.spec.containers:
                    container = pod.spec.containers[0]  # 假设只取第一个容器
                    if container.resources and container.resources.limits:
                        limits = container.resources.limits
                        cpu_limit = limits.get("cpu", "未设置")
                        memory_limit = limits.get("memory", "未设置")
                        gpu_limit = limits.get("nvidia.com/gpu", "未设置")  # 只支持 NVIDIA GPU


                # ✅ 获取 metrics 数据（已有逻辑不变）
                cpu_usage = pod_metrics.get(pod_name, {}).get('cpu', 'undefined')
                if cpu_usage and isinstance(cpu_usage, str):
                    cpu_usage = int(cpu_usage.replace("n", ""))
                    cpu_usage = f'{(cpu_usage / 1000000 / 1000):.3f}核'
                memory_usage = pod_metrics.get(pod_name, {}).get('memory', 'undefined')
                if memory_usage and isinstance(memory_usage, str):
                    memory_usage = int(memory_usage.replace("Ki", ""))
                    memory_usage = f"{(memory_usage / 1024):.3f}Mi"

                if phase in ["Pending", "Succeeded", "Failed"]:
                    cpu_usage = "Pod未运行,无资源使用数据"
                    memory_usage = "Pod未运行,无资源使用数据"


                # ✅ 新增 GPU 使用情况字段（暂时用占位符）
                gpu_usage = "0%"  # 如果你有 DCGM / Prometheus 可替换为实际值
                pod_info = {
                    "pod_namespace": namespace,
                    "pod_name": pod_name,
                    "pod_ready": ready_status,
                    "pod_running": phase,
                    "pod_restart": str(restart_count),
                    "pod_age": pod_age,
                    "pod_ip": pod_ip,
                    "pod_node": node_name,
                    "pod_nominated_node": nominated_node,
                    "pod_cpurate": cpu_usage,
                    "pod_memrate": memory_usage,
                    # ✅ 新增字段
                    "pod_cpu_limit": cpu_limit,
                    "pod_memory_limit": memory_limit,
                    "pod_gpu_limit": gpu_limit,
                    "pod_gpu_usage": gpu_usage,
                }
                rows.append(pod_info)

        result = {
            "total": len(rows),
            "rows": rows
        }
        return result
    except Exception as e:
        raise "获取Pod信息失败: %s" % e.reason
    
    

if __name__ == "__main__":
    kubeconfig = """apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWUyZ0F3SUJBZ0lJTGd4THlGMjM3QmN3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TlRBME1ETXdOelE1TXpWYUZ3MHpOVEEwTURFd056VTBNelZhTUJVeApFekFSQmdOVkJBTVRDbXQxWW1WeWJtVjBaWE13Z2dFaU1BMEdDU3FHU0liM0RRRUJBUVVBQTRJQkR3QXdnZ0VLCkFvSUJBUURQUm5hdkZmNXBTWWUvVmJLc0s2SnhEazhyc2hsc2h5WnNNRk8xZDVhZG45Z055T0wwR2NtbEsrQ1EKVklKSnF3RklJeSsxUVlEd3VRMytzczEwYmV2Y2lqM1BRanluaXJRRkNhRlA0NHh2ZkEyK2thV1FYeTVncGwrMwpjSkI1K1MxVmx2Vi9aSHQ5SXgwNjFCdHB4dE5oMUkxNS9IYk4rWmVNNnEvd3lxUW93Y01ub2pyNDltYkxxOWNwCnFSem5LL2FwWXlBYnljUk9uWWlIZ0FjQWdsclFOTjBKUEJZd2dRd0pIUmlIcGhtVFBkdmY2ckxkNFR0dFl2OXgKdmZIRDNjVUdwZkVBUElaNUJBVi9ZM3p5V0pSbDQzSFV2Ri9jemNDQ01jOVlUd3VXaEpxb2doUUZUdnNuSVZzTwovNEtKQzRwQXFSenJlZFRWdExmMXgzQlRpVCt0QWdNQkFBR2pXVEJYTUE0R0ExVWREd0VCL3dRRUF3SUNwREFQCkJnTlZIUk1CQWY4RUJUQURBUUgvTUIwR0ExVWREZ1FXQkJUZjRZbzBpOVpIZC9ObzdkYWZrZVRTbzVzdzN6QVYKQmdOVkhSRUVEakFNZ2dwcmRXSmxjbTVsZEdWek1BMEdDU3FHU0liM0RRRUJDd1VBQTRJQkFRRERLalJWVVp1YwppckJ4QWdZWnBBeW5NSHdWQTF6YStVT09FM1U0MEMyVTN0VGgrK1BsN2o2ZGJZTWNWdEFvTXhxaDRiVjNQRW5SCmtWcWNaN2NjS3FGSXduZlhHK0ZGTVVwazVoTk0xLzc2UXBobi9OWk8zSStSVjFtV0VOU1BzM1FZdEVoWktXUlgKYWRXZ0krK0x1cUZyZVpTVzVjRXNnMWZDODFtd3dhTXdkRHZWcFJZMFEwWlBsMGFqTURsSlNDaDNOSXpQOS82bwpndXBrY1JSdWtvRGlscWVraXlrRWJ5OVJCWHZIbXo3Q0sxQ1ZnZXZJTDZrVnRPRFF2Rm10Qm1WemlRNWFDcXJOCmtZNmd6OUNGMkdKc2M4UkZrcWQxbzdMelhPakJsTkdzN2k2WmdEOE1Ca2tiank2RmZDZWVndmxOOGFCU2VmblEKZ2ZNOVptbnRpMVNDCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K
    server: https://192.168.0.3:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
current-context: kubernetes-admin@kubernetes
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURJRENDQWdpZ0F3SUJBZ0lIVGZPdmU4TzBJVEFOQmdrcWhraUc5dzBCQVFzRkFEQVZNUk13RVFZRFZRUUQKRXdwcmRXSmxjbTVsZEdWek1CNFhEVEkxTURRd016QTNORGt6TlZvWERUSTJNRFF3TXpBM05UUXpOMW93TkRFWApNQlVHQTFVRUNoTU9jM2x6ZEdWdE9tMWhjM1JsY25NeEdUQVhCZ05WQkFNVEVHdDFZbVZ5Ym1WMFpYTXRZV1J0CmFXNHdnZ0VpTUEwR0NTcUdTSWIzRFFFQkFRVUFBNElCRHdBd2dnRUtBb0lCQVFEWVJJT3h0TWFkOWs2T1JsL1UKZ2ZnZVJDQkpjZmMrc2ZFbzkxeW4vc05KZFVIbWRuamtMaC9wRjcwZkdoVWZ3R2t5dzR0WkdpTFFNR0xwclpyeAphVTdJT0R3a3I2ejl1SkQzaHlFZExhZGpZT0NOMHJhUFNpV05GV1QwSVN2UVBjZzNGQkQ2YmFHb2RtSmN5YnBPCk5qY1VZZmh5WEVqRXMwOU92QzhhZUJCbm9Na1RkRk53dlFaYXE2LzR3eTUyN0k3aUdIUVdvL21JS1VUVHhzRFgKMzJnVXErZmRVMEh5STJJeWhNMGdwT29uNURCVmRUbWsyMkZsVHk0ZWJ3Q3R4QmMvRCtpelhuZFpVd2tHMExMVwpqTEc4L3JkWTZ4WFJDVkhHM1BWNURRK0JvNEpnMTUwWWFSUnBKeDJYSGxad3N5OFBZcWVLcTM0b1pxczRTRndmCjJCY3JBZ01CQUFHalZqQlVNQTRHQTFVZER3RUIvd1FFQXdJRm9EQVRCZ05WSFNVRUREQUtCZ2dyQmdFRkJRY0QKQWpBTUJnTlZIUk1CQWY4RUFqQUFNQjhHQTFVZEl3UVlNQmFBRk4vaGlqU0wxa2QzODJqdDFwK1I1TktqbXpEZgpNQTBHQ1NxR1NJYjNEUUVCQ3dVQUE0SUJBUUFTR0phc1EyQXpLdVNZWFdtMGlYOUhnWTNZQUJGMHpYRzRKZU5lCjREekxkOHF2TXlqRGMwUWFWSUtNbWswemhrV1ZIQzNKSEZWalRXcDBUNFE0TlVBMk8rOXFob1p0a25NL3dsQlUKS0Zab3ZHNFd6SU1sdVJwL21ZRUIzL3dHbkFPV01MdEtBSWJ3d3FRVWl4VW5KYkxCeG4xQ1k5ZERzb1o4VmZZMQp4N2R0WDBJWjJkbU1ETTVLV1lrbW5tQWJBR0tXazZBR3pVWEpWNmlTU3laYjlWLzNuN3hmZlpZRkVDQXBQNk91CjhmRGdIVjBCdEMxS3VmU0tsTitLMnF2aXAzMlRjRHdoTEVHQWQ2aU9qYzhBRXlHelJmOWY4M0xUSGJ2dGtibjYKR0VQQlBQSExSTFlQWEh0OE9LbHdNOThwQWxkSkIyWEJ6UEttc0JFeGFOSWRXd2FTCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K
    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFcEFJQkFBS0NBUUVBMkVTRHNiVEduZlpPamtaZjFJSDRIa1FnU1hIM1BySHhLUGRjcC83RFNYVkI1blo0CjVDNGY2UmU5SHhvVkg4QnBNc09MV1JvaTBEQmk2YTJhOFdsT3lEZzhKSytzL2JpUTk0Y2hIUzJuWTJEZ2pkSzIKajBvbGpSVms5Q0VyMEQzSU54UVErbTJocUhaaVhNbTZUalkzRkdINGNseEl4TE5QVHJ3dkduZ1FaNkRKRTNSVApjTDBHV3F1ditNTXVkdXlPNGhoMEZxUDVpQ2xFMDhiQTE5OW9GS3ZuM1ZOQjhpTmlNb1ROSUtUcUorUXdWWFU1CnBOdGhaVTh1SG04QXJjUVhQdy9vczE1M1dWTUpCdEN5MW95eHZQNjNXT3NWMFFsUnh0ejFlUTBQZ2FPQ1lOZWQKR0drVWFTY2RseDVXY0xNdkQyS25pcXQrS0dhck9FaGNIOWdYS3dJREFRQUJBb0lCQVFDQ1djRjZ3YmdaQzVWTApvZFV1MCt1RjZvLy9WS2F1YmpncDlmWXQ5NXNqVW42Vzl2OWtvUHh3MVBNVHBQZm9mR09yeWpyYVNLdUZDalVFCkhiUlBINmJ4ZlJ1YkRSdmFqWDByQkpLTDhMRjhiNjdKTEtFR2VxMXBmT1N0VkxVQXZjeElqbHF4WnBUU1loQmwKVnQxcE9MbzRHZGpTclJiYklDeUVDMTdrdUV0QytZV3lFb3E5MmlLNVdMTHdHM2hwVzhyVlVLVzZ2T0cyd0l4bAp0RWhMSGpOOWtnb1VVa2pORG9tK2FlcVVxeXhDeUZEdll4UmdhVTd0Y3pJSk52SUk3aDYxaExQbEZtMmxGQ0xlCjhjeTdKUDMyV1ZDSUpUMHhRNkJJRTdvVld4WWIvMzFVSHYrTHg0UHlBcFpiZ3piMjlvQm54VjhneUxnVjZDWW0Kd1psQlQ4S2hBb0dCQU9tMFZqTkVHVm5EaXNsTDFVVkNKYzFCVU1KcjNwalQvV0g4d2s0UzJYWmhwRWdVQmpQYgpDM3Y5czkxNHh6SjhXYWFtUFZPVGZMRmxzRWFLNnJpMFhjQkhXQi9ob1R1aDVKaDByS1RNWWFMTm9SdU00VCt6Ci9zUG1aY1ZMVXcxdHFmd3U5YlVpSTJCQURQNFM2MUFubk5hSnF1UmFWRk8vT1pqZUkvbHJzMVBSQW9HQkFPem0KVTNvcjNuSDh4WHI2WDNJUjRDM3l3TkZLaHNVVE44VmdWNWRVL0U5RmRHTldUVzRkWHdCK01jeUlQMlFLbjlycwpmcU9Cb0c3NlRKVHF0YzVobjY5Q014c1lVNVdPcDhOZW9oaXplY1luSTFjTk94TmZwdzZDdUZVb1pmTFFxU1dICmJ4dEVEaFkrcXJjR2FLZ3VzMk1uMkJ2cEg1bUhCTk5DL05pSVZ1WTdBb0dBZFlnVEhkOHVuSjBockJCdUpsR1kKN3p2YzRKb2RMV0RYZWpNQ2lQOGp6RXhZc1VNWXgzVnV0aUdtRmtpS2JWSnFSOHdzNVY0MEJJY3VlcHVjWmQyWApsSDZNekNQTjBVNmV4eWxPTmVidlowL2dxUmxWb3BMa0dpTkJwVkkzWjNaeVdYaElhNXJLamJwSWpuSjNVeTFJCnpBQWFLSk5nKzJrZEQwc1FibnlDaURFQ2dZQVFDZVA2OEg5bDdqd2NnRmozNnhmblpIa0RjbTAvYUhhdEtVR2sKNEQ4WXl0WC9aN2RrVGg3QmRNbkFWRFVlZTgyb3o3d2ZLOGFGM1BKVVhyT2lYbCttU1BBVzFJWE1LVlZZVjg3WApwMGNHVUY0SEpjRXJKWjIwME1yVUVTRWQyRnlyU3NrTjZvU2RvdTZCNTdBc09zVXdZR0UwT290R0pLc0I5cFlSCnZ1RkxRd0tCZ1FEZVFuRElPaUQ2SEpmc2loTC8xZ3dnS0hVeVc2WGYrNFhQODd3ZlVXT1N0SEpza29oTkZHdk8KSnpNdUFvc2V2UGFWdElCSXBZbFgycUlaaHlhdyt2VW9BUTZYRnR3WjM1QWo1T1VPbVFQQUJWbkVXZUJZRzdSaQpaZmhEU2NTek5xb3ozWFpjMnA4a2VMWE1XOWJsTDNNOTdOMFRLbExuZ0NrSTdoaXJMVGE2T0E9PQotLS0tLUVORCBSU0EgUFJJVkFURSBLRVktLS0tLQo="""

    # 加载配置
    # kubeconfig = yaml.safe_load(kubeconfig)
    # config.load_kube_config_from_dict(kubeconfig)
    # 测试获取节点信息
    # try:
    #     node_info = get_node_info(kubeconfig)
    #     print(json.dumps(node_info, indent=4, ensure_ascii=False))
    # except Exception as e:
    #     print(f"Error: {e}")
    try:
        pod_info = get_pod_info(kubeconfig)
        print(json.dumps(pod_info, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
    
