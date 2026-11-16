---
name: pcapi-repo
version: 1.0.0
description: pcapi 仓库：116 个文件，主语言Python 26，Shell 20，YAML 7
trigger_conditions:
  - 需要理解、修改或排障 pcapi 的代码
  - 在 pcapi 里定位入口、数据表、对外契约或构建方式
---

# pcapi 仓库技能

> 由仓库实际内容生成的骨架（README/目录/模型定义/契约/构建脚本逐项取证）。新增判断与坑位请直接在下面对应小节补充。

## 定位

**pcapi**

* 将sqlor,ahserver,apppublic,rbac,appbase库拉取下来依次安装 上述代码用来包装k8s的以下功能 将下面的代码放在def init_func()函数的最后： 有新功能需要扩充时,请参照上述功能操作 paramify(data, ns): data是一个python的字符串,字典或数组,其中的数据有用“${name}$"形式定义的变量,此函数将data中的参数用ns字典中的值替换 此函数在dspy脚本中可用 curl --basic --user kyycloud:Kyy@123456 https://pcapi.opencomputing.cn

- 远端：`https://github.com/yumoqing/pcapi.git`
- 默认分支：`main`（共 51 个提交）
- 最近提交：2026-11-03 `d35496a` chore: 忽略 init/logs 等生成物
- 规模：116 个文件；Python 26，Shell 20，YAML 7

## 目录结构

- `wwwroot/` — 前端页面与 `.dspy` 契约（服务端渲染入口）（45 个文件）
- `app/` — 应用级初始化 / 菜单与页面装配（24 个文件）
- `script/` — 脚本（17 个文件）
- `files/` — 静态文件（14 个文件）
- `deploy/` — 部署脚本/编排（5 个文件）
- `k8s_doc/` — 2 个文件
- `pcapi/` — Python 包源码（模块本体）（2 个文件）
- `conf/` — 配置（`config.json`；密码为 AES 密文）（1 个文件）
- `logs/` — 1 个文件
- `script_test/` — 1 个文件
- 根文件：`.gitignore`、`README.md`、`install.sh`、`requirements.txt`

## 对外契约（`.dspy`，40 个）

- `wwwroot/api/v1/`：4 个 — create_pod.dspy、get_available_resources.dspy、resource_enough.dspy、server_instance_delete.dspy
- `wwwroot/api/v1/cluster/common/delete_cluster_node/`：1 个 — index.dspy
- `wwwroot/api/v1/cluster/common/delete_cluster_pod/`：1 个 — index.dspy
- `wwwroot/api/v1/cluster/common/delete_cpcpod/`：1 个 — index.dspy
- `wwwroot/api/v1/cluster/common/determine_accommodat/`：1 个 — index.dspy
- `wwwroot/api/v1/cluster/common/get_cluster_nodes/`：1 个 — index.dspy
- `wwwroot/api/v1/cluster/common/get_cluster_pods/`：1 个 — index.dspy
- `wwwroot/api/v1/cluster/common/multiple_cluster/`：1 个 — index.dspy

## 构建与运行

- `requirements.txt`：3 项（git+https://git.kaiyuancloud.cn/yumoqing/apppublic、git+https://git.kaiyuancloud.cn/yumoqing/sqlor、git+https://git.kaiyuancloud.cn/yumoqing/ahserver）
- Python 包 `pcapi/`：`cluster_resource_monitor_with_pid_mapping.py`、`vm_buckup_restore.py`

## README 要点与注意（摘自 `README.md`）

- 章节：安装须知、安全保证、服务方代码、请求方代码例子
- 注意：建议不要直接pip install -r requirement.txt,小麻烦较多

## 建议阅读顺序

1. `README.md`
2. `wwwroot/`

