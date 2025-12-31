#!/bin/bash
set -e
# https://org.ngc.nvidia.com/setup/api-keys
# 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
# =================配置区域=================
get_script_path(){
	# 获取脚本真实路径（解析软链接）
	SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
	echo "$SCRIPT_DIR"
}
MYPATH=$(get_script_path)
ARCH=amd64
WORKDIR=${MYPATH}/k8s-offline-bundle
K8S_VERSION="1.28.2"
HELM_VERSION="v3.13.1"
CNI_VERSION="v1.3.0"
CALICO_VERSION="v3.26.1"
KUBEVIRT_VERSION="v1.1.0" # 升级到更稳定的版本
NVIDIA_DRIVER_VERSION="535.129.03"
# =========================================

echo ">>> [0/6] 初始化目录..."
mkdir -p $WORKDIR/{bin,service, debs,images,drivers,charts,manifests,scripts}

echo ">>>[x] 下载containerd.service"
cd $WORKDIR/service
sudo curl -L https://raw.githubusercontent.com/containerd/containerd/main/containerd.service -o containerd.service

PKGS_TO_DOWNLOAD="nfs-common socat conntrack ipset ebtables lvm2 gnupg2 software-properties-common curl ca-certificates apt-transport-https"
cd $WORKDIR/debs
sudo apt-get update -q
for pkg in $PKGS_TO_DOWNLOAD; do
    echo "Processing package: $pkg"
    # 使用 apt-rdepends 找出依赖并下载 (需要先安装: sudo apt install apt-rdepends)
    # 如果没有 apt-rdepends，可以用简化的 apt-get download，但可能漏掉深层依赖
    # 这里使用一种更通用的方法，尝试下载包本身
    apt-get download "$pkg" 2>/dev/null || echo "Warning: Failed to download $pkg"
done
apt-get download build-essential linux-headers-$(uname -r) pkg-config 2>/dev/null
# 然后使用 apt-get download 下载包及其所有依赖
sudo apt-get download nvidia-container-toolkit libnvidia-container-tools libnvidia-container1 nvidia-container-runtime cuda-keyring
ls -l $WORKDIR/debs

# 检查 Docker 是否存在 (下载镜像必须)
if ! command -v docker &> /dev/null; then
    echo "正在安装 Docker (用于拉取镜像)..."
    apt-get update && apt-get install -y docker.io
fi

# ================= 1. 二进制文件 =================
echo ">>> [1/6] 下载二进制工具 (Helm, CNI)..."
cd $WORKDIR/bin

# 1. Kubernetes Binaries (kubelet, kubeadm, kubectl)
curl -L --retry 3 https://dl.k8s.io/v${K8S_VERSION}/bin/linux/${ARCH}/kubeadm -o kubeadm
curl -L --retry 3 https://dl.k8s.io/v${K8S_VERSION}/bin/linux/${ARCH}/kubelet -o kubelet
curl -L --retry 3 https://dl.k8s.io/v${K8S_VERSION}/bin/linux/${ARCH}/kubectl -o kubectl
chmod +x kubeadm kubelet kubectl

# Helm
if [ ! -f "helm" ]; then
    echo "Downloading Helm..."
    wget -q https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz
    tar -zxvf helm-${HELM_VERSION}-linux-amd64.tar.gz
    mv linux-amd64/helm .
    rm -rf linux-amd64 helm-*.tar.gz
fi

# CNI Plugins
if [ ! -f "cni-plugins-linux-amd64-${CNI_VERSION}.tgz" ]; then
    echo "Downloading CNI Plugins..."
    wget -q https://github.com/containernetworking/plugins/releases/download/${CNI_VERSION}/cni-plugins-linux-amd64-${CNI_VERSION}.tgz
fi

echo "Binaries ready."

# ================= 2. 容器镜像 =================
echo ">>> [2/6] 拉取并打包容器镜像 (这需要较长时间)..."
# 确保 Docker 守护进程在运行
service docker start || true

# 定义镜像列表
# 包含: K8s 核心, Calico, Multus, KubeVirt, NFS, Nvidia相关
# 注意: Pause 镜像版本需与 kubeadm config 中一致
NVIDIA_REPO="nvcr.io/nvidia"
IMAGES=(
    "registry.k8s.io/kube-apiserver:v${K8S_VERSION}"
    "registry.k8s.io/kube-controller-manager:v${K8S_VERSION}"
    "registry.k8s.io/kube-scheduler:v${K8S_VERSION}"
    "registry.k8s.io/kube-proxy:v${K8S_VERSION}"
    "registry.k8s.io/pause:3.9"
    "registry.k8s.io/etcd:3.5.12-0"
    "registry.k8s.io/coredns/coredns:v1.10.1"
    "docker.io/calico/cni:${CALICO_VERSION}"
    "docker.io/calico/node:${CALICO_VERSION}"
    "docker.io/calico/kube-controllers:${CALICO_VERSION}"
    "docker.io/library/registry:2"
    "ghcr.io/k8snetworkplumbingwg/multus-cni:v4.0.2"
    "quay.io/kubevirt/virt-operator:${KUBEVIRT_VERSION}"
    "quay.io/kubevirt/virt-api:${KUBEVIRT_VERSION}"
    "quay.io/kubevirt/virt-controller:${KUBEVIRT_VERSION}"
    "quay.io/kubevirt/virt-handler:${KUBEVIRT_VERSION}"
    "quay.io/kubevirt/virt-launcher:${KUBEVIRT_VERSION}"
    "registry.k8s.io/sig-storage/nfs-subdir-external-provisioner:v4.0.2"
    "nvcr.io/nvidia/k8s-device-plugin:v0.14.1"
)

# ${NVIDIA_REPO}/container-toolkit:v1.13.5-ubuntu20.04
# ${NVIDIA_REPO}/dcgm-exporter:3.2.5-3.1.7-ubuntu20.04
# ${NVIDIA_REPO}/gpu-feature-discovery:v0.8.1
# ${NVIDIA_REPO}/driver:535.104.05-ubuntu22.04

cd $WORKDIR/images
for img in "${IMAGES[@]}"; do
    # 将 / 和 : 替换为 _ 作为文件名
    FILENAME=$(echo $img | tr '/:' '__').tar
    if [ -f "$FILENAME" ]; then
        echo "跳过已存在: $FILENAME"
    else
        echo "Pulling $img ..."
        docker pull $img
        echo "Saving to $FILENAME ..."
        docker save $img -o $FILENAME
        # 节省空间，保存后删除本地 docker缓存
        docker rmi $img
    fi
done

# ================= 3. NVIDIA 驱动 =================
echo ">>> [3/6] 下载 NVIDIA H100 驱动 (.run)..."
cd $WORKDIR/drivers
DRIVER_NAME="NVIDIA-Linux-x86_64-${NVIDIA_DRIVER_VERSION}.run"
if [ ! -f "$DRIVER_NAME" ]; then
    echo "Downloading NVIDIA Driver..."
    wget -q https://us.download.nvidia.com/tesla/${NVIDIA_DRIVER_VERSION}/${DRIVER_NAME}
fi

# ================= 4. YAML Manifests =================
echo ">>> [4/6] 下载 K8s YAML 配置文件..."
cd $WORKDIR/manifests

# Calico
curl -L -o calico.yaml https://raw.githubusercontent.com/projectcalico/calico/${CALICO_VERSION}/manifests/calico.yaml

# KubeVirt
KUBEVIRT_REL="https://github.com/kubevirt/kubevirt/releases/download/${KUBEVIRT_VERSION}"
curl -L -o kubevirt-operator.yaml ${KUBEVIRT_REL}/kubevirt-operator.yaml
curl -L -o kubevirt-cr.yaml ${KUBEVIRT_REL}/kubevirt-cr.yaml

# Multus
curl -L -o multus-daemonset.yaml https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/master/deployments/multus-daemonset.yml

# ================= 5. Helm Charts =================
echo ">>> [5/6] 下载 Helm Charts..."
cd $WORKDIR/charts

# 添加 repo (如果 helm 命令可用)
if command -v helm &> /dev/null; then
    helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/
    helm repo update
    helm pull nfs-subdir-external-provisioner/nfs-subdir-external-provisioner --version 4.0.18
else
    echo "Helm not installed on host, downloading chart directly via wget..."
    wget -q https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner/releases/download/nfs-subdir-external-provisioner-4.0.18/nfs-subdir-external-provisioner-4.0.18.tgz
fi

# ================= 6. 验证 =================
echo "---------------------------------------------"
echo ">>> 下载工作全部完成！正在统计文件大小..."
cd $WORKDIR
du -sh *
echo "---------------------------------------------"
echo "请检查 debs 目录是否依然有文件 (这是之前下载的)。"
echo "images 目录应该有几 GB 大小。"
echo "drivers 目录应该有 400MB+。"
cd ${MYPATH}
tar cvf - k8s-offline-bundle master-install.sh worker-install.sh | gzip > k8s-offline-bundle.tgz

