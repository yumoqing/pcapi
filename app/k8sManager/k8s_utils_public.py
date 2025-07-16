import yaml
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from appPublic.log import debug
import time
import re
import json
import ast

def format_source_labels(source_selflabel, type=None):
    """
    格式化源标签（支持多个 key-value）
    :param source_selflabel: 源标签字符串，格式如：
                            pod类型: "key1:value1,key2:value2"
                            node类型: "key3=value3,key4=value4"
    :param type: 标签类型 ("pod" 或 "node")
    :return: 格式化后的标签字典 {key: value}
    """
    if not source_selflabel or len(source_selflabel.strip()) == 0:
        return {}
    label_dict = {}
    if type == "pod":
        # Pod 标签使用冒号分隔，多个用逗号分隔
        for pair in source_selflabel.strip().split(","):
            if ":" in pair:
                key, value = pair.strip().split(":", 1)
                label_dict[key.strip()] = value.strip()
    elif type == "node":
        # Node 标签使用等号分隔，多个用逗号分隔
        for pair in source_selflabel.strip().split(","):
            if "=" in pair:
                key, value = pair.strip().split("=", 1)
                label_dict[key.strip()] = value.strip()
    else:
        return {}
    return label_dict

def format_runtime(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes}m"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours}h"
    else:
        days = int(seconds // 86400)
        return f"{days}d"

def extract_model_labels(hardware_list):
    """ 
    提取硬件列表中的模型标签为列表，
    :param hardware_list: 硬件列表，格式如：
    kyy-gpu-model=RTX5090-32G,kyy-cpu-model=INTEL(R) XEON(R) PLATINUM 8582C
    """
    labels = []
    for item in hardware_list:
        if item["type"] in {"cpu", "gpu"}:
            labels.append(f"kyy-{item['type']}-model={item['model'].replace(' ','-').replace('(','-').replace(')','-').replace('kyy-','')}")
    return labels

def determine_accommodat(kubeconfig,get_resources):
    """ 
    判断产品资源是否可以被当前集群容纳
    磁盘除外，因为磁盘资源通常是通过 PV/PVC 管理的，不在节点资源统计中。
    :param kubeconfig: kubeconfig 配置
    :param get_resources: 产品资源字典，格式如：
                     {
                        "5436-f-gdsb--ewrewrerrtwt": [
                            {
                                "type": "cpu",
                                "model": "INTEL(R) XEON(R) PLATINUM 8582C",
                                "amount": 0
                            },
                            {
                                "type": "memory",
                                "model": "Samsung DDR4 DIMMs",
                                "amount": 0
                            },
                            {
                                "type": "disk",
                                "model": "DATA",
                                "amount": 0
                            },
                            {
                                "type": "gpu",
                                "model": "RTX5090-32G",
                                "amount": 0
                            }
                        ],
                        "6787jhgvgjhv32412343142jvgj": [
                            {
                                "type": "cpu",
                                "model": "INTEL(R) XEON(R) PLATINUM 8582C",
                                "amount": 4
                            },
                            {
                                "type": "memory",
                                "model": "Samsung DDR4 DIMMs",
                                "amount": 100
                            },
                            {
                                "type": "disk",
                                "model": "DATA",
                                "amount": 512
                            },
                            {
                                "type": "gpu",
                                "model": "RTX5090-32G",
                                "amount": 2
                            }
                        ],
                    }
    : params kyylabels: 节点自定义标签，格式如 "key1:value1,key2:value2"
    :return: 可容纳的产品 ID 列表
    """
    init_ids = []
    try:
        all_quota = get_node_info(kubeconfig).get('rows', [])
        if not all_quota:
            debug("determine_accommodat: 没有获取到节点信息")
            return init_ids

        products = {}
        if isinstance(get_resources, str):
            debug(f"---get_resources格式:{type(get_resources)}")
            products = json.loads(get_resources)
            # debug(f"1---products格式:{type(products)}")
            if isinstance(products, str):
                products = eval(products)
                debug(f"2---products格式:{type(products)}")
            
        all_quota = [x for x in all_quota if x['node_status'] != '未就绪' and x['node_role'] != 'master']
        debug(f"\n 接收请求资源={products},\n 现有资源:{all_quota}")

        # 预处理节点数据，转换为数值类型
    
        processed_nodes = []
        for node in all_quota:
            # 跳过不可用节点和控制节点
            if node['node_status'] != '已就绪' or node['node_role'] == 'master':
                #debug(f"跳过未就绪节点/控制节点:{node['node_internalip']} {node['node_status']} {node['node_name']}")
                continue
            
            # 提取可用CPU（去除"核"字并转换为float）
            cpu_str = node['available_cpu'].replace('核', '')
            available_cpu = float(cpu_str)
            
            # 提取可用内存（处理Gi单位）
            mem_str = node['available_memory']
            if mem_str.endswith('Gi'):
                available_memory = float(mem_str.replace('Gi', ''))
            else:
                # 假设其他单位为Mi并转换为Gi
                available_memory = float(mem_str.replace('Mi', '')) / 1024
            
            available_gpu = node['available_gpu']
            
            processed_nodes.append({
                'node_name': node['node_name'],
                'node_labels': node['node_labels'],  # 节点自定义标签
                'cpu': available_cpu,
                'memory': available_memory,
                'gpu': available_gpu
            })

        # 找出无法部署的产品ID
        init_ids = []
        for product_id, resources in products.items():
            # 提取产品资源需求
            product_cpu = next((r['amount'] for r in resources if r['type'] == 'cpu'), 0)
            product_memory = next((r['amount'] for r in resources if r['type'] == 'memory'), 0)
            product_gpu = next((r['amount'] for r in resources if r['type'] == 'gpu'), 0)
            
            # 管理员视角创建Pod的时候，CPU的请求单位可能是毫核(m)也可能是Gi，如果是m则转成核
            if "m" in str(product_cpu):
                product_cpu = float(product_cpu.replace("m", "")) / 1000.0

            # 管理员视角创建Pod的时候，内存的请求单位可能带了单位Gi，如果是1G则转成1.0
            if "Gi" in str(product_memory):
                product_memory = float(product_memory.replace("Gi", ""))
            elif "Mi" in str(product_memory):
                product_memory = float(product_memory.replace("Mi", "")) / 1024.0

            # 管理员视角创建Pod的时候，磁盘的请求单位可能是带了单位Gi，如果是1G则转成1.0
            # 这里磁盘不在节点资源统计中，所以不处理
            # if "Gi" in str(product_disk):
            #     product_disk = float(product_disk.replace("Gi", ""))
            # elif "Mi" in str(product_disk):
            #     product_disk = float(product_disk.replace("Mi", "")) / 1024

            # 检查是否存在任何节点可以满足该产品需求(这里规定，不能完全占满，只能略小于，毕竟节点上可能还有其他服务会动态占用资源)
            can_deploy = False
            for node in processed_nodes:
                #此处转换标签并给出判断该节点此标签产品是否可部署
                kyy_labels = extract_model_labels(resources)
                if kyy_labels:
                    # 检查节点标签是否包含产品所需的标签
                    if not all(label in node['node_labels'] for label in kyy_labels):
                        debug(f"节点 {node['node_name']} 不满足产品 {product_id} 的标签要求: {kyy_labels}")
                        continue
                
                    debug(f'✅ 请求标签在其中节点选择器标签范围内,可部署: {kyy_labels}')

                debug(f"核心参数判断：{product_cpu=} {node['cpu']=} # {float(product_memory)=} {node['memory']=} # {float(product_gpu)=} {node['gpu']=}")
                if (product_cpu < node['cpu'] and float(product_memory) < node['memory'] and float(product_gpu) <= node['gpu']):
                    can_deploy = True
                    break
            
            if not can_deploy:
                init_ids.append(product_id)

        debug(f"无法在集群任何节点上部署的产品ID: {init_ids}")
        return init_ids
    except:
        import traceback
        debug(f"创建异常: {traceback.format_exc()}")
        raise f"determine_accommodat 异常: {traceback.format_exc()}"

def get_pod_info(kubeconfig): 
    try:
        # config.load_kube_config()
        kubeconfig = yaml.safe_load(kubeconfig)
        config.load_kube_config_from_dict(kubeconfig)
        v1 = client.CoreV1Api()
        api_client = client.ApiClient()

        namespaces = v1.list_namespace(timeout_seconds=1).items
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
            
            # debug(f"### pods={pods}")
            for pod in pods:
                pod_name = pod.metadata.name
                if pod.status.container_statuses:
                    ready_count = sum(1 for cs in pod.status.container_statuses if cs.ready)
                else:
                    ready_count = 0

                # 获取容器总数
                total_containers = len(pod.spec.containers)
                # 计算就绪容器数
                ready_count = 0
                if pod.status.container_statuses:
                    ready_count = sum(1 for status in pod.status.container_statuses if status.ready)
                # 计算就绪比例
                ready_ratio = ready_count / total_containers if total_containers > 0 else 0
                # 判断就绪状态
                ready_status = "已就绪" if ready_ratio >= 1 else "未就绪"
                
                # 抛弃下面这种写法，极端情况下集合操作会出问题
                # ready_status = "已就绪" if ({ready_count}/{len(pod.spec.containers)}) >= 1 else "未就绪"

                readiness_conditions = [{"type": cond.type, "status": cond.status}
                                        for cond in pod.status.conditions if cond.type == "Ready"]
                phase = pod.status.phase
                restart_count = sum(cs.restart_count for cs in pod.status.container_statuses) if pod.status.container_statuses else 0
                running_time = time.time() - pod.metadata.creation_timestamp.timestamp()
                pod_age = format_runtime(running_time)
                pod_ip = pod.status.pod_ip if pod.status.pod_ip else "Unknown"
                node_name = pod.spec.node_name if pod.spec.node_name else "Pod未被调度到节点"
                nominated_node = pod.status.nominated_node_name if pod.status.nominated_node_name else "无"

                if phase == "Pending":
                    pod_ip = "Pending状态,未分配 IP"
                    node_name = "Pending状态,未分配节点"
                    nominated_node = "Pending状态,未分配节点"

                #  提取容器的资源限制（limits）
                cpu_limit = "未设置"
                memory_limit = "未设置"
                gpu_limit = "未设置"

                if pod.spec.containers:
                    container = pod.spec.containers[0]  # 假设只取第一个容器
                    if container.resources and container.resources.limits:
                        limits = container.resources.limits
                        cpu_limit = limits.get("cpu", "未设置")  # 假设 CPU 限制以核为单位
                        # 处理特殊情况,如果 CPU 限制以毫核(m)为单位，转换为核
                        # debug(f'cpu_limit==={cpu_limit}')
                        if isinstance(cpu_limit, str) and cpu_limit.endswith("m"):
                            debug(f'无法识别的cpu_limit格式:{cpu_limit} 转换为 {float((int(cpu_limit.replace("m", "")) / 1000))}核')
                            cpu_limit = f'{float((int(cpu_limit.replace("m", "")) / 1000))}'
                        memory_limit = limits.get("memory", "未设置")
                        gpu_limit = limits.get("nvidia.com/gpu", "未设置")  # 只支持 NVIDIA GPU


                #  获取 metrics 数据（已有逻辑不变）
                cpu_usage = pod_metrics.get(pod_name, {}).get('cpu', 'undefined')
                if cpu_usage and isinstance(cpu_usage, str):
                    cpu_usage = int(cpu_usage.replace("n", "")) if cpu_usage.endswith("n") else 0
                    cpu_usage = f'{(cpu_usage / 1000000 / 1000):.3f}核'
                memory_usage = pod_metrics.get(pod_name, {}).get('memory', 'undefined')
                if memory_usage and isinstance(memory_usage, str):
                    memory_usage = int(memory_usage.replace("Ki", "")) if memory_usage.endswith("Ki") else 0
                    memory_usage = f"{(memory_usage / 1024 / 1024):.3f}Gi"

                if phase in ["Pending", "Succeeded", "Failed"]:
                    cpu_usage = "Pod未运行,无资源使用数据"
                    memory_usage = "Pod未运行,无资源使用数据"


                #  新增 GPU 使用情况字段（暂时用占位符）
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
                    #  新增字段
                    "pod_gpu": gpu_limit,
                    "pod_cpu_limit": cpu_limit + "核" if cpu_limit != "未设置" else "未设置",
                    "pod_memory_limit": memory_limit,
                    "pod_gpu_limit": gpu_limit,
                }
                rows.append(pod_info)

        result = {
            "total": len(rows),
            "rows": rows
        }
        return result
    except Exception as e:
        import traceback
        debug(f"获取Pod信息失败: {traceback.format_exc()}")
        raise traceback.format_exc()

def get_node_info(kubeconfig):
    # 加载配置
    try:
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
        pods = v1.list_pod_for_all_namespaces(timeout_seconds=1).items
        node_pod_resources = {}  # 存储每个节点上 Pod 的资源请求
        
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
            roles_str = "master" if roles else "worker"
            
            # 节点运行时间
            running_time = time.time() - node.metadata.creation_timestamp.timestamp()
            node_age = format_runtime(running_time)
        
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
                "node_name": node_name,
                "node_status": status,
                "node_role": roles_str,
                "node_age": node_age,
                "node_version": k8s_version,
                "node_internalip": internal_ip,
                "node_externalip": external_ip,
                "node_osversion": os_image,
                "node_kernelversion": kernel_version,
                "node_containeruntime": container_runtime,
                "node_labels": kyy_labels,
                "node_cpurate": f"{(allocated_cpu / total_cpu * 100):.1f}%" if total_cpu > 0 else "0%",#cpu_usage,
                "node_memrate": f"{(allocated_memory / total_memory * 100):.1f}%" if total_memory > 0 else "0%",#memory_usage,
                "node_gpu":f"{(allocated_gpu / total_gpu * 100):.1f}%" if total_gpu > 0 else "0%",
                # 新增资源信息
                # "node_total_cpu": f"{total_cpu:.2f}核",
                # "allocated_cpu": f"{allocated_cpu:.2f}核",
                "available_cpu": f"{available_cpu:.2f}核",
                # "cpu_rate": f"{(allocated_cpu / total_cpu * 100):.1f}%" if total_cpu > 0 else "0%",
                
                # "node_total_memory": f"{total_memory:.2f}Gi",
                # "allocated_memory": f"{allocated_memory:.2f}Gi",
                "available_memory": f"{available_memory:.2f}Gi",
                # "memory_rate": f"{(allocated_memory / total_memory * 100):.1f}%" if total_memory > 0 else "0%",
                
                # "node_total_gpu": total_gpu,
                # "allocated_gpu": allocated_gpu,
                "available_gpu": available_gpu,
                # "gpu_rate": f"{(allocated_gpu / total_gpu * 100):.1f}%" if total_gpu > 0 else "0%"
            }
            rows.append(node_info)
         
        result = {
            "total": len(rows),
            "rows": rows
        }
        debug(f"=== node_info={result}")
        return result
    except:
        import traceback
        e = traceback.format_exc()
        debug(f"获取节点信息失败: {e}")
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