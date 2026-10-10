#!/bin/bash

set -euo pipefail

# 始终从服务目录启动；所有提示写入stderr，避免污染stdio协议。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PYTHON="$SCRIPT_DIR/mcp_env/bin/python"

echo "启动HandaaS展会MCP服务器..." >&2

# 检查虚拟环境
if [ ! -x "$PYTHON" ]; then
    echo "错误: 虚拟环境不存在，请先在 $SCRIPT_DIR 运行 python -m venv mcp_env" >&2
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "警告: .env文件不存在，请确保已通过环境变量配置API认证信息" >&2
    echo "需要配置 INTEGRATOR_ID、SECRET_ID、SECRET_KEY" >&2
fi

# 安装依赖
echo "检查Python依赖..." >&2
"$PYTHON" -m pip install -q -r "$SCRIPT_DIR/requirements.txt" -c "$SCRIPT_DIR/constraints.txt" >&2

# 启动服务器
echo "启动展会MCP服务器..." >&2
exec "$PYTHON" "$SCRIPT_DIR/server/mcp_server.py" "${1:-stdio}"
