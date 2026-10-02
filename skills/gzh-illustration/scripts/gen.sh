#!/usr/bin/env bash
# agnes-ai 生图脚本（gzh-illustration 技能用）
# 用法：gen.sh "prompt" 输出路径.png [size] [model]
# key 从库内 raw/assets/agnes-ai.md 读取（git 忽略区），不进命令行明文。
set -euo pipefail

PROMPT="${1:?用法：gen.sh \"prompt\" 输出路径.png [size] [model]}"
OUT="${2:?缺少输出路径}"
SIZE="${3:-1792x1024}"
MODEL="${4:-agnes-image-2.5-flash}"
KEY_FILE="${AGNES_KEY_FILE:-$HOME/.zcode/workspace/default/obsidian/raw/assets/agnes-ai.md}"

[ -f "$KEY_FILE" ] || { echo "凭证文件不存在：$KEY_FILE" >&2; exit 1; }
KEY=$(grep -oP '(?<=API Key：)sk-\S+' "$KEY_FILE") || true
[ -n "${KEY:-}" ] || { echo "从 $KEY_FILE 提取 key 失败" >&2; exit 1; }

REQ=$(mktemp); RESP=$(mktemp); trap 'rm -f "$REQ" "$RESP"' EXIT
python3 -c '
import json, sys
req, model, size, prompt = sys.argv[1:5]
open(req, "w").write(json.dumps(
    {"model": model, "prompt": prompt, "n": 1, "size": size, "response_format": "b64_json"},
    ensure_ascii=False))' "$REQ" "$MODEL" "$SIZE" "$PROMPT"

HTTP=$(curl -s --max-time 170 https://api.agnes-ai.cn/v1/images/generations \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d @"$REQ" -o "$RESP" -w "%{http_code}")
[ -s "$RESP" ] || { echo "接口无响应（HTTP $HTTP）" >&2; exit 1; }

python3 -c '
import json, sys, base64, urllib.request
resp, out = sys.argv[1:3]
d = json.load(open(resp))
item = (d.get("data") or [None])[0]
if not item:
    sys.exit("生成失败 HTTP " + sys.argv[3] + " " + json.dumps(d, ensure_ascii=False)[:400])
if item.get("b64_json"):
    open(out, "wb").write(base64.b64decode(item["b64_json"]))
elif item.get("url"):
    urllib.request.urlretrieve(item["url"], out)
else:
    sys.exit("返回中无 b64_json/url 字段 " + json.dumps(item, ensure_ascii=False)[:200])
print("已保存", out)' "$RESP" "$OUT" "$HTTP"
