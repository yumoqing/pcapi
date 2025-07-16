def ssh_execute_commands(host, port, username, password, commands, real_time_log=False):
    try:
        import paramiko
        # 创建 SSH 对象
        ssh = paramiko.SSHClient()
        # 允许连接不在 know_hosts 文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接服务器
        ssh.connect(hostname=host, port=port, username=username, password=password)
        all_results = []
        result = ""
        error = ""
        for command in commands:
        #     stdin, stdout, stderr = ssh.exec_command(f'sudo -S {command}', get_pty=True)
        #     stdin.write(password + '\n')
            stdin, stdout, stderr = ssh.exec_command(f'{command}', get_pty=True)
            stdin.flush()
            if real_time_log:
                print(f"开始执行命令: {command}")
                # 实时读取标准输出
                for line in iter(stdout.readline, ""):
                    print(line, end="")
                    result += line
                # 实时读取标准错误输出
                for line in iter(stderr.readline, ""):
                    print(line, end="")
                    error += line
            else:
                result = stdout.read().decode()
                error = stderr.read().decode()

            all_results.append((result, error))
            if real_time_log:
                print(f"命令 {command} 执行结束")

        # 关闭连接
        ssh.close()
        return all_results
    except Exception as e:
        print(f"SSH 连接或执行命令时出错: {e}")
        return None

def new_cluster(params):
    # 随后填充远程操控k8s主逻辑
    """
        用于接收cpcc端传递过来的k8s安装指令参数，进行远程sshx调用操作内网机器进行集群节点的安装
        参数示例：
        {'cluster_type': '0', 'host': '192.168.0.3', 'port': '22', 'user': 'ysh', 'password': 'Kyy@123456'}
    """
    host = params.get("host")
    port = int(params.get("port"))
    username = params.get("user")
    password = params.get("password")
    commands = ['kubectl get nodes', 'kubectl get pods --all-namespaces', 'kubectl get services --all-namespaces']
    results = ssh_execute_commands(host, port, username, password, commands, real_time_log=True)
    if results:
        # print("所有命令执行的整体结果：")
        for result, error in results:
            if result:
                print("执行结果：")
                print(result)
            if error:
                print("错误信息：")
                print(error)
    return results


import json
import argparse
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import time


def setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


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


def get_node_info():
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        api_client = client.ApiClient()
        node_metrics_path = "/apis/metrics.k8s.io/v1beta1/nodes"

        nodes = v1.list_node().items
        node_metrics_response = api_client.call_api(
            node_metrics_path, 'GET', auth_settings=['BearerToken'], response_type='object')[0]
        node_metrics = {node['metadata']['name']: node.get('usage', {})
                        for node in node_metrics_response.get('items', [])}

        rows = []
        for node in nodes:
            node_name = node.metadata.name
            internal_ip = next((address.address for address in node.status.addresses
                               if address.type == "InternalIP"), "Unknown")
            external_ip = next((address.address for address in node.status.addresses
                               if address.type == "ExternalIP"), "Unknown")
            status = node.status.conditions[-1].status if node.status.conditions else "Unknown"
            roles = []
            role_labels = [
                "node-role.kubernetes.io/control-plane",
                "node-role.kubernetes.io/master",
                "node-role.kubernetes.io/worker"
            ]
            for label in role_labels:
                if label in node.metadata.labels:
                    roles.append(label.split("/")[-1])
            roles_str = ",".join(roles) if roles else "None"
            running_time = time.time() - node.metadata.creation_timestamp.timestamp()
            node_age = format_runtime(running_time)
            k8s_version = node.status.node_info.kubelet_version
            os_image = node.status.node_info.os_image
            kernel_version = node.status.node_info.kernel_version
            container_runtime = node.status.node_info.container_runtime_version
            labels = node.metadata.labels

            cpu_usage = node_metrics.get(node_name, {}).get('cpu', 'undefined')
            memory_usage = node_metrics.get(node_name, {}).get('memory', 'undefined')

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
                "node_labels": labels,
                "node_cpurate": cpu_usage,
                "node_memrate": memory_usage
            }
            rows.append(node_info)

        result = {
            "total": len(rows),
            "rows": rows
        }
        return result
    except ApiException as e:
        logging.error(f"获取节点信息时出错: {e}")
        return {"total": 0, "rows": []}


def get_pod_info():
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        api_client = client.ApiClient()

        namespaces = v1.list_namespace().items
        non_system_namespaces = [ns.metadata.name for ns in namespaces if
                                 not ns.metadata.name.startswith(('kube-', 'default', 'local'))]

        rows = []
        for namespace in non_system_namespaces:
            pods = v1.list_namespaced_pod(namespace).items
            pod_metrics_path = f"/apis/metrics.k8s.io/v1beta1/namespaces/{namespace}/pods"
            pod_metrics_response = api_client.call_api(
                pod_metrics_path, 'GET', auth_settings=['BearerToken'], response_type='object')[0]
            pod_metrics = {pod['metadata']['name']: pod.get('usage', {})
                           for pod in pod_metrics_response.get('items', [])}

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
                pod_age = format_runtime(running_time)
                pod_ip = pod.status.pod_ip if pod.status.pod_ip else "Unknown"
                node_name = pod.spec.node_name if pod.spec.node_name else "Pod 未被调度到节点"
                nominated_node = pod.status.nominated_node_name if pod.status.nominated_node_name else "调度器未提名节点"

                if phase == "Pending":
                    pod_ip = "Pod 处于 Pending 状态，未分配 IP"
                    node_name = "Pod 处于 Pending 状态，未被调度到节点"
                    nominated_node = "Pod 处于 Pending 状态，调度器未提名节点"

                readiness_gates = []

                cpu_usage = pod_metrics.get(pod_name, {}).get('cpu', 'undefined')
                memory_usage = pod_metrics.get(pod_name, {}).get('memory', 'undefined')

                if phase in ["Pending", "Succeeded", "Failed"]:
                    cpu_usage = "Pod 未运行，无资源使用数据"
                    memory_usage = "Pod 未运行，无资源使用数据"

                pod_info = {
                    "pod_namespace": namespace,
                    "pod_name": pod_name,
                    "pod_ready": ready_status,
                    "pod_running": phase,
                    "pod_restart": restart_count,
                    "pod_age": pod_age,
                    "pod_ip": pod_ip,
                    "pod_node": node_name,
                    "pod_nominated_node": nominated_node,
                    "pod_readiness_gates": readiness_gates,
                    "pod_cpurate": cpu_usage,
                    "pod_memrate": memory_usage
                }
                rows.append(pod_info)

        result = {
            "total": len(rows),
            "rows": rows
        }
        return result
    except ApiException as e:
        logging.error(f"获取Pod信息时出错: {e}")
        return {"total": 0, "rows": []}



if __name__ == "__main__":
#     params = {'cluster_type': '0', 'host': '192.168.0.3', 'port': '22', 'user': 'root', 'password': 'Yuanshenhong.1'}
#     new_cluster(params)
    parser = argparse.ArgumentParser(description='获取Kubernetes节点和Pod实时信息')
    parser.add_argument('--interval', type=int, default=300, help='刷新间隔（秒）')
    args = parser.parse_args()

    setup_logging()
    while True:
        node_info = get_node_info()
        pod_info = get_pod_info()

        result = {
            "节点信息": node_info,
            "Pod信息": pod_info
        }

        logging.info(json.dumps(result, indent=4, ensure_ascii=False))

        time.sleep(args.interval)
    