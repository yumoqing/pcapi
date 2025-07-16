#!/bin/bash

nfs_dynamic_yaml=""
while IFS= read -r line; do
	nfs_dynamic_yaml+="$line\n"  # 手动添加换行符
  done < ../files/nfs-provisioner-deploy.yaml

  echo -e "内容：\n$nfs_dynamic_yaml"

echo "$nfs_dynamic_yaml" | kubectl apply -f -
    if [ $? -ne 0 ]; then
        echo "资源创建失败"
        exit 1
    fi
  