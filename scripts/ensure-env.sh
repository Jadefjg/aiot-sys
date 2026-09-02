#!/usr/bin/env bash
# 将环境模板中的键合并进 .env：仅补充缺失项，不覆盖已有值（保留密码等）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODE="${1:-}"
ENV_FILE="${ROOT}/.env"

usage() {
  cat <<'EOF'
用法: ./scripts/ensure-env.sh <local|production|shared>

  local       — 本地开发（.env.example）
  production  — 阿里云全栈 Docker（.env.production.example）
  shared      — 阿里云共享 MySQL/Redis（.env.shared.example）

git 不跟踪 .env；本脚本只补全缺失配置键，不会覆盖已有密码与域名。
EOF
}

pick_template() {
  case "$MODE" in
    local) echo "${ROOT}/.env.example" ;;
    production) echo "${ROOT}/.env.production.example" ;;
    shared) echo "${ROOT}/.env.shared.example" ;;
    *) usage; exit 1 ;;
  esac
}

TEMPLATE="$(pick_template)"
if [[ ! -f "$TEMPLATE" ]]; then
  echo "模板不存在: $TEMPLATE" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$TEMPLATE" "$ENV_FILE"
  echo "已创建 .env <- $(basename "$TEMPLATE")"
  exit 0
fi

# 读取 .env 已有键
declare -A EXISTING=()
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$line" || "$line" != *=* ]] && continue
  key="${line%%=*}"
  key="$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  EXISTING["$key"]=1
done < "$ENV_FILE"

added=0
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  trimmed="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$trimmed" || "$trimmed" != *=* ]] && continue
  key="${trimmed%%=*}"
  key="$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  if [[ -z "${EXISTING[$key]+x}" ]]; then
    echo "$trimmed" >> "$ENV_FILE"
    echo "+ $key"
    ((added++)) || true
  fi
done < "$TEMPLATE"

echo "完成：新增 ${added} 项，已有键未改动。"
