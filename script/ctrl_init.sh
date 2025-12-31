sudo kubeadm init --kubernetes-version=v1.29.0 --pod-network-cidr=10.244.0.0/16
# 保存 kubeconfig
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

kubectl apply -f /opt/offline/kubevirt/kubevirt-operator.yaml
kubectl apply -f /opt/offline/kubevirt/kubevirt-cr.yaml

kubeadm token create --print-join-command
