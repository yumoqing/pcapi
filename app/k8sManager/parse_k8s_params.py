import re
import json


def parse_k8s_pods(input_text):
    header_mapping = {
        "NAMESPACE": "pod_namespace",
        "NAME": "pod_name",
        "READY": "pod_ready",
        "STATUS": "pod_running",
        "RESTARTS": "pod_restart",
        "AGE": "pod_age",
        "IP": "pod_ip",
        "NODE": "pod_node",
        "NOMINATED NODE": "pod_nominated_node",
        "READINESS GATES": "pod_readiness_gates"  # 检查列名映射
    } 
    
    lines = [line.strip() for line in input_text.strip().split('\n')]
    if not lines:
        return {"total": 0, "rows": []}
    
    raw_headers = re.split(r'\s{2,}', lines[0])
    rows = []
    for line in lines[1:]:
        values = re.split(r'\s{2,}', line.strip())
        if len(values) == len(raw_headers):
            mapped = {}
            for i, raw_h in enumerate(raw_headers):
                if raw_h in header_mapping:
                    mapped[header_mapping[raw_h]] = values[i]
            rows.append(mapped)
    
    return {
        "total": len(rows),
        "rows": rows
    }


def parse_k8s_nodes(input_text):
    # 定义表头映射关系（原始表头 -> 目标字段名）
    header_mapping = {
        "NAME": "node_name",
        "STATUS": "node_status",
        "ROLES": "node_role",
        "AGE": "node_age",
        "VERSION": "node_version",
        "INTERNAL-IP": "node_internalip",
        "EXTERNAL-IP": "node_externalip",
        "OS-IMAGE": "node_osversion",
        "KERNEL-VERSION": "node_kernelversion",
        "CONTAINER-RUNTIME": "node_containeruntime",
        "LABELS":"node_labels",
    }

    lines = [line.strip() for line in input_text.strip().split('\n')]
    
    # 处理表头（应用映射关系）
    raw_headers = re.split(r'\s{2,}', lines[0])
    headers = [header_mapping[h] for h in raw_headers if h in header_mapping]  # 确保只保留存在映射的字段
    
    rows = []
    for line in lines[1:]:
        values = re.split(r'\s{2,}', line.strip())
        if len(values) == len(raw_headers):  # 使用原始表头长度进行匹配（保持列数一致）
            # 按原始表头顺序映射到目标字段名
            mapped_values = {header_mapping[raw_headers[i]]: values[i] for i in range(len(raw_headers)) if raw_headers[i] in header_mapping}
            rows.append(mapped_values)
    
    result = {
        "total": len(rows),
        "rows": rows
    }

    return result

if __name__ == "__main__":
# 示例输入（你的 kubectl 输出）
    input_text1 = '''NAME         STATUS   ROLES           AGE     VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
    k8s-master   Ready    control-plane   4d19h   v1.28.2   192.168.0.3   <none>        Ubuntu 22.04.1 LTS   5.15.0-91-generic   containerd://1.7.24'''

    # 执行转换
    # output1 = parse_k8s_nodes(input_text1)
    # print(output1)
    input_text2 = '''NAMESPACE     NAME                               READY   STATUS    RESTARTS   AGE     IP            NODE                     NOMINATED NODE   READINESS GATES
kube-flannel  kube-flannel-ds-sbkgm              1/1     Running   0          14m     192.168.0.2   k8s-worker-20250408132243 <none>           <none>'''

    result = parse_k8s_pods(input_text2)
    print(json.dumps(result, indent=2))



