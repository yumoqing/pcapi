#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
备份前建议关机或确保数据一致性
恢复前 VM 应该处于关机状态
只处理 disk0，多磁盘可扩展循环处理
GPU VM 也适用，恢复 PVC 后可重新分配 GPU
"""
import os
import sys
import argparse
import subprocess
import yaml
from kubernetes import client, config

# ----------------------------
# 参数解析
# ----------------------------
parser = argparse.ArgumentParser(description="KubeVirt VM Backup and Restore (NFS, Multi-disk, GPU)")
parser.add_argument("action", choices=["backup","restore"], help="操作类型")
parser.add_argument("--vm", required=True, help="VM 名称")
parser.add_argument("--namespace", default="default", help="VM 所在 Namespace")
parser.add_argument("--nfs-path", required=True, help="共享 NFS 路径，例如 /mnt/nfs-backup")
parser.add_argument("--restore-vm", help="恢复时新 VM 名称，如果不填覆盖原 VM")
args = parser.parse_args()

vm_name = args.vm
namespace = args.namespace
nfs_path = args.nfs_path
restore_vm_name = args.restore_vm or vm_name

# ----------------------------
# 初始化 K8s API
# ----------------------------
try:
    kubeconfig_path = os.environ.get("KUBECONFIG","/root/.kube/config")
    config.load_kube_config(config_file=kubeconfig_path)
except Exception as e:
    print(f"加载 kubeconfig 失败: {e}")
    sys.exit(1)

v1 = client.CoreV1Api()
crd_api = client.CustomObjectsApi()

# ----------------------------
# 获取 virt-launcher Pod
# ----------------------------
def get_virt_launcher_pod(vm, ns):
    pods = v1.list_namespaced_pod(namespace=ns, label_selector=f"kubevirt.io=virt-launcher,vm={vm}")
    if not pods.items:
        print(f"未找到 VM {vm} 的 virt-launcher Pod")
        sys.exit(1)
    return pods.items[0].metadata.name

# ----------------------------
# 获取 VM spec（包括 nodeSelector, GPU 配置）
# ----------------------------
def get_vm_spec(vm, ns):
    vm_obj = crd_api.get_namespaced_custom_object(
        group="kubevirt.io",
        version="v1",
        namespace=ns,
        plural="virtualmachines",
        name=vm
    )
    return vm_obj.get("spec", {}).get("template", {}).get("spec", {})

# ----------------------------
# 备份 VM
# ----------------------------
def backup_vm():
    pod_name = get_virt_launcher_pod(vm_name, namespace)
    backup_dir = os.path.join(nfs_path, vm_name)
    os.makedirs(backup_dir, exist_ok=True)

    # 获取磁盘路径
    cmd_list_disks = f"kubectl exec -n {namespace} {pod_name} -- ls /var/run/kubevirt-private/vmi-disks/"
    disks = subprocess.check_output(cmd_list_disks, shell=True).decode().splitlines()

    for disk in disks:
        src_path = f"/var/run/kubevirt-private/vmi-disks/{disk}"
        dest_path = os.path.join(backup_dir, f"{disk}.qcow2")
        print(f"[备份] {disk} -> {dest_path}")
        # 转换成 QCOW2 临时文件
        cmd_convert = f"kubectl exec -n {namespace} {pod_name} -- qemu-img convert -O qcow2 {src_path} /tmp/{disk}.qcow2"
        subprocess.run(cmd_convert, shell=True, check=True)
        # 拷贝到 NFS
        cmd_cp = f"kubectl cp {namespace}/{pod_name}:/tmp/{disk}.qcow2 {dest_path}"
        subprocess.run(cmd_cp, shell=True, check=True)
        # 清理临时文件
        subprocess.run(f"kubectl exec -n {namespace} {pod_name} -- rm /tmp/{disk}.qcow2", shell=True)
    print(f"VM {vm_name} 备份完成，存放在 {backup_dir}")

# ----------------------------
# 恢复 VM
# ----------------------------
def restore_vm():
    backup_dir = os.path.join(nfs_path, vm_name)
    if not os.path.exists(backup_dir):
        print(f"备份目录 {backup_dir} 不存在")
        sys.exit(1)

    # 获取原 VM spec
    original_spec = get_vm_spec(vm_name, namespace)

    # 删除原 VM（如果覆盖）
    if restore_vm_name == vm_name:
        print(f"[恢复] 删除原 VM {vm_name}，请确保 VM 已关机")
        subprocess.run(f"kubectl delete vm {vm_name} -n {namespace}", shell=True, check=True)

    # 创建 PVC 并上传 QCOW2
    disk_files = [f for f in os.listdir(backup_dir) if f.endswith(".qcow2")]
    for i, disk_file in enumerate(disk_files):
        pvc_name = f"{restore_vm_name}-disk{i}"
        pvc_yaml = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": pvc_name, "namespace": namespace},
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": "100Gi"}},
                "storageClassName": "nfs-sc"
            }
        }
        pvc_file_path = f"/tmp/{pvc_name}.yaml"
        with open(pvc_file_path, "w") as f:
            yaml.dump(pvc_yaml, f)
        subprocess.run(f"kubectl apply -f {pvc_file_path}", shell=True, check=True)

    # 创建新的 VM YAML
    vm_yaml = {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachine",
        "metadata": {"name": restore_vm_name, "namespace": namespace},
        "spec": {"running": True, "template": {"spec": original_spec}}
    }
    vm_file = f"/tmp/{restore_vm_name}.yaml"
    with open(vm_file, "w") as f:
        yaml.dump(vm_yaml, f)
    subprocess.run(f"kubectl apply -f {vm_file}", shell=True, check=True)

    # 上传 QCOW2 到 virt-launcher Pod
    pod_name = get_virt_launcher_pod(restore_vm_name, namespace)
    for i, disk_file in enumerate(disk_files):
        qcow_path = os.path.join(backup_dir, disk_file)
        pvc_disk_path = f"/var/run/kubevirt-private/vmi-disks/disk{i}"
        print(f"[恢复] 上传 {qcow_path} -> {pvc_disk_path}")
        cmd_cp = f"kubectl cp {qcow_path} {namespace}/{pod_name}:{pvc_disk_path}"
        subprocess.run(cmd_cp, shell=True, check=True)

    print(f"VM {restore_vm_name} 恢复完成，可启动")

# ----------------------------
# 主函数
# ----------------------------
if args.action == "backup":
    backup_vm()
elif args.action == "restore":
    restore_vm()

