#!/bin/bash/

# 设置 Kubernetes 版本和镜像仓库地址
K8S_VERSION="v1.28.2"
ALIYUN_REGISTRY="registry.aliyuncs.com/google_containers"  # 阿里云 Kubernetes 镜像源
FLANNEL_REPO="ghcr.io/flannel-io"  # Flannel 镜像仓库
NETWORK_PLUGIN="flannel"
NETWORK_PLUGIN_VERSION="v0.26.4"
NETWORK_PLUGIN_CNI="flannel-cni-plugin"
NETWORK_PLUGIN_CNI_VERSION="v1.6.2-flannel1"

# Kubernetes 控制平面镜像列表（阿里云镜像源）
KUBERNETES_IMAGES=(
  "${ALIYUN_REGISTRY}/kube-apiserver:${K8S_VERSION}"
  "${ALIYUN_REGISTRY}/kube-controller-manager:${K8S_VERSION}"
  "${ALIYUN_REGISTRY}/kube-scheduler:${K8S_VERSION}"
  "${ALIYUN_REGISTRY}/kube-proxy:${K8S_VERSION}"
  "${ALIYUN_REGISTRY}/pause:3.9"
  "${ALIYUN_REGISTRY}/etcd:3.5.9-0"
  "${ALIYUN_REGISTRY}/coredns:v1.10.1"
)

# 网络插件镜像（Flannel）
NETWORK_IMAGES=(
  "${FLANNEL_REPO}/${NETWORK_PLUGIN}:${NETWORK_PLUGIN_VERSION}"
)
NETWORK_CNI_IMAGES=(
  "${FLANNEL_REPO}/${NETWORK_PLUGIN_CNI}:${NETWORK_PLUGIN_CNI_VERSION}"
)

# 合并所有镜像
ALL_IMAGES=("${KUBERNETES_IMAGES[@]}" "${NETWORK_IMAGES[@]}" "${NETWORK_CNI_IMAGES[@]}")

# 导出本地已存在的镜像（在源节点运行）
function export_images() {
  echo "==> 正在导出本地已存在的 Kubernetes v${K8S_VERSION} 镜像..."
  mkdir -p /opt/k8s-images
  cd /opt/k8s-images || exit

  for image in "${ALL_IMAGES[@]}"; do
    echo "正在检查并导出镜像：${image}"
    if ctr -n=k8s.io images list --quiet | grep -q "${image}"; then
      output_file="${image//\//_}.tar"
      ctr -n=k8s.io images export ${output_file} ${image} --platform=linux/amd64
      echo "✅ 成功导出：${output_file}"
    else
      echo "⚠️ 镜像 ${image} 不存在于本地,跳过！"
    fi
  done
}

# 根据需要选择执行导出或导入
export_images   # 在源节点运行,导出镜像