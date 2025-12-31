# deploy-kubevirt-and-gpu.sh
# 在主控节点运行
# 加载镜像
docker load -i /tmp/images/gpu-operator-images.tar
docker load -i /tmp/images/kubevirt-images.tar

# 安装 Helm
tar -xzf /tmp/helm/helm.tar.gz -C /tmp/
cp /tmp/linux-amd64/helm /usr/local/bin/helm

# 添加仓库（离线无需 add）
helm install gpu-operator nvidia/gpu-operator \
  --version=v24.9.0 \
  --set driver.enabled=false \  # 已手动安装驱动
  --set toolkit.enabled=true \
  --set devicePlugin.enabled=true \
  --set dcgmExporter.enabled=true \
  --set migManager.enabled=true \
  --set operator.defaultRuntime=containerd

# 等待 GPU 就绪
watch kubectl get pods -n gpu-operator-resources

# 安装 KubeVirt
kubectl create namespace kubevirt
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.1.0/kubevirt-operator.yaml
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.1.0/kubevirt-cr.yaml

# 安装 CDI（用于导入镜像）
helm install cdi kubevirt/cdi --namespace kubevirt --version=v1.50.0

# 配置 NFS 动态供给（可选）
kubectl apply -f nfs-client-provisioner.yaml  # 自定义配置指向你的 100T NFS
