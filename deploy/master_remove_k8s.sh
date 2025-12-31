#!/usr/bin/env bash
set -e

echo "=== Starting Kubernetes Master Node Cleanup ==="
echo "WARNING: This script will irrevocably delete all Kubernetes data, configuration,"
echo "         AND YOUR LOCAL DOCKER REGISTRY'S DATA from this node."
echo "         DO NOT RUN ON A PRODUCTION CLUSTER!"
echo ""
echo "--- Step 0: Stopping and Cleaning Local Docker Registry ---"
# 假设你的 Registry 容器名为 'registry'，并且端口是 5000
# 如果你的 Registry 容器名或端口不同，请修改这里
LOCAL_REGISTRY_CONTAINER_NAME="registry"

# 停止并删除 Registry 容器
sudo docker stop "$LOCAL_REGISTRY_CONTAINER_NAME" || { echo "❌ Local Registry container stop failed or not found, but continuing..."; }
# -v 选项会删除与容器关联的所有匿名数据卷。
# 如果你使用了具名数据卷（例如：-v my-registry-data:/var/lib/registry），
# 你可能需要手动删除它：sudo docker volume rm my-registry-data
sudo docker rm -v "$LOCAL_REGISTRY_CONTAINER_NAME" || { echo "❌ Local Registry container removal failed or not found, but continuing..."; }

echo "  Local Docker Registry container stopped and removed."

echo "--- Step 1: Resetting kubeadm ---"
sudo kubeadm reset -f || { echo "❌ kubeadm reset failed or encountered errors, but continuing..."; }

echo "--- Step 2: Stopping and cleaning containerd (CRI Runtime) ---"
sudo systemctl stop containerd || { echo "❌ containerd service stop failed, but continuing..."; }

sudo ctr -n k8s.io containers ls -q | xargs -r sudo ctr -n k8s.io containers rm || true
sudo ctr -n default containers ls -q | xargs -r sudo ctr -n default containers rm || true

# 彻底删除 containerd 的镜像数据和配置文件 (强烈推荐)
sudo rm -rf /var/lib/containerd/* || { echo "❌ Failed to clean /var/lib/containerd, but continuing..."; }
sudo rm -rf /etc/containerd/* || { echo "❌ Failed to clean /etc/containerd, but continuing..."; }

echo "--- Step 3: Cleaning CNI network configurations ---"
sudo rm -rf /etc/cni/net.d/* || { echo "❌ Failed to clean /etc/cni/net.d, but continuing..."; }
sudo rm -rf /var/lib/cni/* || { echo "❌ Failed to clean /var/lib/cni, but continuing..."; }

echo "--- Step 4: Cleaning kubelet related files ---"
sudo rm -rf /var/lib/kubelet/* || { echo "❌ Failed to clean /var/lib/kubelet, but continuing..."; }
sudo rm -rf /var/run/kubernetes/* || { echo "❌ Failed to clean /var/run/kubernetes, but continuing..."; }

echo "--- Step 5: Removing Kubernetes configuration files ---"
sudo rm -rf ~/.kube || { echo "❌ Failed to clean ~/.kube, but continuing..."; }
sudo rm -rf /etc/kubernetes/* || { echo "❌ Failed to clean /etc/kubernetes, but continuing..."; }

echo "--- Step 6: Cleaning up iptables and IPVS rules ---"
sudo iptables -F
sudo iptables -t nat -F
sudo iptables -t raw -F
sudo iptables -t mangle -F
sudo iptables -X

if command -v ipvsadm &> /dev/null; then
    sudo ipvsadm --clear || { echo "❌ Failed to clear ipvsadm rules, but continuing..."; }
fi

# 确保删除所有由 Docker daemon 自身创建的 K8s 相关网络（如果 Registry 运行在 Docker 上，并且 Docker daemon 也被 K8s 使用过）
# 再次注意：这一步通常在 K8s 节点上执行时安全，但需谨慎
sudo docker network ls -q | grep -E 'k8s|cni' | xargs -r sudo docker network rm || true

echo ""
echo "=== Kubernetes Master Node Cleanup COMPLETED ==="
echo "It is HIGHLY RECOMMENDED to reboot this node now to ensure a completely clean state."
echo "You can do this by running: sudo reboot"
echo ""

sudo systemctl daemon-reload
