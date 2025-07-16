#!/bin/bash

# 设置 Kubernetes 版本和镜像仓库地址
K8S_VERSION="v1.28.2"
ALIYUN_REGISTRY="registry.aliyuncs.com/google_containers"  # 阿里云 Kubernetes 镜像源
HANGZHOU_ALIYUN_REGISTRY="registry.cn-hangzhou.aliyuncs.com/google_containers"  # 杭州阿里云镜像站
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
  "${ALIYUN_REGISTRY}/metrics-server:v0.7.2"
  "${HANGZHOU_ALIYUN_REGISTRY}/kube-webhook-certgen:v1.1.1"
  "${HANGZHOU_ALIYUN_REGISTRY}/nginx-ingress-controller:v1.5.1"
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

# 导入镜像并自动修复配置（在目标节点运行）
function import_images() {
  echo "==> 正在导入镜像到目标节点..."

  # 2. 停止 containerd 服务
  sudo systemctl stop containerd

  # 3. 进入镜像目录
  cd /opt/k8s-images || exit

  # 4. 清理旧镜像（根据你的镜像仓库地址过滤）
  echo "正在清理旧镜像..."
  for img in $(ctr -n=k8s.io images list --quiet); do
    if [[ $img == ${ALIYUN_REGISTRY}* || $img == ${FLANNEL_REPO}* || $img == ${HANGZHOU_ALIYUN_REGISTRY}* ]]; then
      ctr -n=k8s.io images rm $img || true
    fi
  done

  sudo systemctl start containerd

  # 5. 导入所有 tar 文件
  for file in *.tar; do
    echo "正在导入镜像：${file}"
    ctr -n=k8s.io images import ${file} --platform=linux/amd64
    echo "✅ 导入成功：${file}"
  done

  # 6. 启动 containerd 并验证
  #sudo systemctl restart containerd
  echo "已导入的镜像列表："
  ctr -n=k8s.io images list | grep -E "${ALIYUN_REGISTRY}|${HANGZHOU_ALIYUN_REGISTRY}|${FLANNEL_REPO}"
  crictl images
}


# 根据需要选择执行导入
import_images   # 在目标节点运行,导入镜像
