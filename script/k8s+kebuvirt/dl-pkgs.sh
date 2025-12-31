#!/bin/bash
# offline-download.sh
# 在有互联网的机器上执行，将所有依赖打包供离线部署使用

set -e
apt install podman-docker
export WORKDIR=/tmp/k8s-offline
for d in packages,images,k8s-binaries,helm,nvidia,gpu-operator,kubevirt
do
	mkdir -p $WORKDIR/$d
done

cd $WORKDIR

echo "=== 下载 Kubernetes 二进制文件 ==="
K8S_VERSION=v1.29.6
ARCH=amd64

curl -L --retry 3 https://dl.k8s.io/${K8S_VERSION}/bin/linux/${ARCH}/kubeadm -o k8s-binaries/kubeadm
curl -L --retry 3 https://dl.k8s.io/${K8S_VERSION}/bin/linux/${ARCH}/kubelet -o k8s-binaries/kubelet
curl -L --retry 3 https://dl.k8s.io/${K8S_VERSION}/bin/linux/${ARCH}/kubectl -o k8s-binaries/kubectl

chmod +x k8s-binaries/*

echo "=== 下载 containerd ==="
CONTAINERD_VERSION=1.7.16
curl -L --retry 3 https://github.com/containerd/containerd/releases/download/v${CONTAINERD_VERSION}/containerd-${CONTAINERD_VERSION}-linux-amd64.tar.gz -o packages/containerd.tar.gz

echo "=== 下载 runc ==="
RUNC_VERSION=v1.1.13
curl -L --retry 3 https://github.com/opencontainers/runc/releases/download/${RUNC_VERSION}/runc.amd64 -o packages/runc && chmod +x packages/runc

echo "=== 下载 CNI 插件 ==="
CNI_VERSION=v1.4.1
curl -L --retry 3 https://github.com/containernetworking/plugins/releases/download/${CNI_VERSION}/cni-plugins-linux-amd64-${CNI_VERSION}.tgz -o packages/cni-plugins.tgz

echo "=== 下载 Helm ==="
HELM_VERSION=v3.13.3
curl -L --retry 3 https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz -o helm/helm.tar.gz

echo "=== 下载 NVIDIA Driver（仅元信息，实际需手动获取）==="
echo "注意：NVIDIA 驱动无法直接 wget，请从官网下载："
echo "https://www.nvidia.com/Download/index.aspx?lang=en-us"
echo "选择 A100-SXM4 / Data Center Driver for Linux x86_64"
echo "保存为: nvidia/NVIDIA-Linux-x86_64-535.161.08.run"

echo "=== 下载 NVIDIA Container Toolkit 依赖（通过 apt 离线包）==="
# 使用 docker pull + save 方式更可靠
echo "准备构建本地 apt repo 或使用 .deb 包方式"

# 推荐方法：在一台联网 Ubuntu 22.04 上执行：
cat > prepare-debs.sh << 'EOF'
#!/bin/bash
mkdir -p /tmp/debs
apt update
apt install -y --download-only curl conntrack socat ipvsadm iptables bridge-utils ethtool git wget tar
apt install -y --download-only nfs-utils nfs-common
apt install -y --download-only nvidia-driver-535 nvidia-utils-535 nvidia-dkms-535
apt install -y --download-only nvidia-container-toolkit
cp /var/cache/apt/archives/*.deb /path/to/offline/nvidia/
EOF

echo "请运行 prepare-debs.sh 获取 .deb 包"

echo "=== 拉取 GPU Operator 所需镜像 ==="
# GPU Operator 会拉取多个镜像，我们预先列出并导出
cat > gpu-operator-images.txt << 'EOF'
nvcr.io/nvidia/gpu-operator:v24.9.0
nvcr.io/nvidia/gpu-feature-discovery:v0.8.0
nvcr.io/nvidia/driver:535.161.08-ubuntu22.04
nvcr.io/nvidia/container-toolkit:1.14.2-ubuntu22.04
nvcr.io/nvidia/dcgm:3.1.7-3-ubuntu22.04
nvcr.io/nvidia/k8s-device-plugin:0.14.2-ubi8
nvcr.io/nvidia/k8s-operator-validator:v1.2.0
EOF

while read img; do
    echo "Pulling $img"
    docker pull $img || echo "Failed: $img"
done < gpu-operator-images.txt

# 保存镜像为 tar 文件
docker save $(cat gpu-operator-images.txt | tr '\n' ' ') -o images/gpu-operator-images.tar

echo "=== 拉取 KubeVirt 组件镜像 ==="
KV_VERSION=v1.1.0
cat > kubevirt-images.txt << EOF
quay.io/kubevirt/virt-operator:${KV_VERSION}
quay.io/kubevirt/virt-api:${KV_VERSION}
quay.io/kubevirt/virt-controller:${KV_VERSION}
quay.io/kubevirt/virt-handler:${KV_VERSION}
quay.io/kubevirt/virt-launcher:${KV_VERSION}
quay.io/kubevirt/cdi-operator:v1.50.0
quay.io/kubevirt/cdi-apiserver:v1.50.0
quay.io/kubevirt/cdi-uploadproxy:v1.50.0
quay.io/kubevirt/cdi-cloner:v1.50.0
quay.io/kubevirt/cdi-importer:v1.50.0
quay.io/kubevirt/cdi-uploadserver:v1.50.0
EOF

while read img; do
    docker pull $img || echo "Failed: $img"
done < kubevirt-images.txt

docker save $(cat kubevirt-images.txt | tr '\n' ' ') -o images/kubevirt-images.tar

echo "=== 创建最终离线包 ==="
tar -czf k8s-offline-all.tar.gz .

echo "✅ 所有离线资源已生成：k8s-offline-all.tar.gz"
echo "请将其复制到目标环境并解压"
