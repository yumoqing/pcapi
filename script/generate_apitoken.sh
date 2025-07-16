#!/bin/bash

# 定义变量
NAMESPACE="my-namespace"
SERVICE_ACCOUNT="my-sa"

# YAML 内容（确保 Deployment 明确使用 ServiceAccount）
all_resources_yaml='
apiVersion: v1
kind: Namespace
metadata:
  name: '"$NAMESPACE"'

---

apiVersion: v1
kind: ServiceAccount
metadata:
  name: '"$SERVICE_ACCOUNT"'
  namespace: '"$NAMESPACE"'

---

apiVersion: v1
kind: Service
metadata:
  name: my-mysql-service
  namespace: '"$NAMESPACE"'
spec:
  type: NodePort
  selector:
    app: mysql
  ports:
    - protocol: TCP
      port: 3306
      targetPort: 3306
      nodePort: 30060

---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql-deployment
  namespace: '"$NAMESPACE"'
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      serviceAccountName: '"$SERVICE_ACCOUNT"'  # 关键：强制 Pod 使用该 ServiceAccount
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: "123456"
        resources:
          limits:
            cpu: "300m"
            memory: "512Mi"
'

# 创建资源函数
create_resources() {
    echo "$all_resources_yaml" | kubectl apply -f -
    if [ $? -ne 0 ]; then
        echo "资源创建失败"
        exit 1
    fi
    # 新增：等待 Secret 生成（最多 10 秒）
    echo "等待 ServiceAccount 的 Secret 生成..."
    for i in {1..10}; do
        local secret_name=$(kubectl get serviceaccount "$SERVICE_ACCOUNT" -n "$NAMESPACE" -o jsonpath='{.secrets[0].name}' 2>/dev/null)
        if [ -n "$secret_name" ]; then
            break
        fi
        sleep 1
    done
}

# 删除资源函数
delete_resources() {
    echo "$all_resources_yaml" | kubectl delete -f -
    if [ $? -ne 0 ]; then
        echo "资源创建失败"
        exit 1
    fi
}

# 获取 Token 函数（优化错误提示）
get_service_account_token() {
    local secret_name=$(kubectl get serviceaccount "$SERVICE_ACCOUNT" -n "$NAMESPACE" -o jsonpath='{.secrets[0].name}' 2>/dev/null)
    if [ -z "$secret_name" ]; then
        echo "错误：ServiceAccount 的 Secret 未生成,请检查 Pod 是否正常运行"
        exit 1
    fi
    local token=$(kubectl get secret -n "$NAMESPACE" "$secret_name" -o jsonpath='{.data.token}' | base64 -d)
    echo "ApiToken: $token"
}

# 执行流程
create_resources
#echo "资源创建完成"
#kubectl get all -n "$NAMESPACE"

#echo "正在获取 ServiceAccount 的 Token..."
#get_service_account_token


#delete_resources