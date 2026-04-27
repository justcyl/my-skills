#!/usr/bin/env bash
# Execution quality eval for grill-me skill
# Tests whether Phase 1/2/3 flow is correctly followed

SKILL_PATH="/Users/chenyl/project/my-skills/grill-me"
MODEL="github-copilot/claude-sonnet-4.6"
LOG_DIR="$(dirname "$0")/results"
mkdir -p "$LOG_DIR"

PLAN_PROMPT='grill me on this plan:

**项目：团队内部知识库系统**

背景：我们是一个 15 人的研发团队，现在文档散落在 Notion、飞书、本地 Markdown 文件和 Confluence 里，很难找到东西。

方案概要：
- 用 Elasticsearch 做全文搜索
- 前端用 React + Ant Design
- 后端用 Go + Gin
- 用 MinIO 存附件
- 部署在内网服务器上

目标：两个月内上线一个内部搜索工具，支持跨平台聚合搜索。'

echo "============================================"
echo "  grill-me 执行质量评测"
echo "  (Phase 1→2→3 流程)"
echo "============================================"
echo ""
echo "输入方案："
echo "$PLAN_PROMPT"
echo ""
echo "正在运行 pi (可能需要 30-60 秒)..."
echo "============================================"

OUTPUT=$(pi --skill "$SKILL_PATH" \
    --model "$MODEL" \
    --no-session \
    --thinking off \
    -p "$PLAN_PROMPT" 2>&1)

echo "$OUTPUT"
echo "$OUTPUT" > "$LOG_DIR/exec_quality.txt"

echo ""
echo "============================================"
echo "  自动化评分检查"
echo "============================================"

SCORE=0
MAX=7

check() {
  local name="$1"
  local pattern="$2"
  if echo "$OUTPUT" | grep -qiE "$pattern"; then
    echo "✅ $name"
    SCORE=$((SCORE + 1))
  else
    echo "❌ $name"
  fi
}

check "Phase 1: 呈现了理解/目标" "(目标|理解|要解决|问题|效果)"
check "Phase 1: 包含方案概要" "(方案|Elasticsearch|Go|React|MinIO|架构)"
check "Phase 1: 包含推断/假设标注" "(推断|假设|猜测|不确定|应该是|可能是)"
check "Phase 1: 提出风险/权衡" "(风险|权衡|问题|挑战|潜在|注意)"
check "Phase 2: 包含批量追问" "(问题[1-9]|Q[1-9]|第[一二三四五六七八九]个问题|追问|[0-9]+\.|[①②③④⑤])"
check "Phase 2: 问题带推荐答案/理由" "(推荐|建议|理由|因为|原因)"
check "Phase 2: 问题说明了影响" "(影响|决定|取决|依赖|重要)"

echo ""
echo "执行质量得分: $SCORE / $MAX"
PCT=$(echo "scale=1; $SCORE * 100 / $MAX" | bc)
echo "得分率: $PCT%"
echo "============================================"

if [ "$SCORE" -ge 6 ]; then
  echo "🏆 优秀 - 流程执行完整"
elif [ "$SCORE" -ge 4 ]; then
  echo "👍 良好 - 基本流程正确，有优化空间"
elif [ "$SCORE" -ge 2 ]; then
  echo "⚠️  一般 - 流程不完整"
else
  echo "❌ 差 - 未按 skill 指令执行"
fi
