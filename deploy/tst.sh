#!/usr/bin/env bash

get_script_path(){
	# 获取脚本真实路径（解析软链接）
	SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
	echo "$SCRIPT_DIR"
}

echo "$(get_script_path)"
