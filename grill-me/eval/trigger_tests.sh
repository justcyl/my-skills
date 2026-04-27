#!/usr/bin/env bash
# Trigger accuracy eval for grill-me skill
# Tests whether the model loads/follows grill-me at appropriate times

SKILL_PATH="/Users/chenyl/project/my-skills/grill-me"
MODEL="github-copilot/claude-sonnet-4.6"
LOG_DIR="$(dirname "$0")/results"
mkdir -p "$LOG_DIR"

PASS=0
FAIL=0
TOTAL=0

run_test() {
  local id="$1"
  local label="$2"
  local expected="$3"   # "yes" = should trigger, "no" = should not trigger
  local prompt="$4"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Test #$id [$expected] $label"
  echo "Prompt: $prompt"
  echo "----------------------------------------"

  OUTPUT=$(pi --skill "$SKILL_PATH" \
      --model "$MODEL" \
      --no-session \
      --thinking off \
      -p "$prompt" 2>&1)

  echo "$OUTPUT" | head -80
  echo "$OUTPUT" > "$LOG_DIR/test_${id}.txt"

  # Heuristic: if output contains Phase 1 keywords → triggered
  # Key markers: "理解", "目标", "方案", "追问", or "推断"
  TRIGGERED="no"
  if echo "$OUTPUT" | grep -qiE "(理解|目标|方案概要|追问|推断|Phase|心智对齐|对齐备忘录|批量|核心决策)"; then
    TRIGGERED="yes"
  fi

  TOTAL=$((TOTAL + 1))
  if [ "$TRIGGERED" = "$expected" ]; then
    echo "✅ PASS (expected=$expected, got=$TRIGGERED)"
    PASS=$((PASS + 1))
  else
    echo "❌ FAIL (expected=$expected, got=$TRIGGERED)"
    FAIL=$((FAIL + 1))
  fi
}

echo "============================================"
echo "  grill-me 触发准确率评测"
echo "============================================"

# --- Should TRIGGER ---
run_test "T1" "直接使用 grill me 短语" "yes" \
  "grill me on this plan: 我想做一个 AI 笔记应用，用 Electron + React 做桌面端，后端用 FastAPI"

run_test "T2" "中文触发：帮我过一下这个方案" "yes" \
  "帮我过一下这个方案：我们团队打算把单体服务拆成微服务，先从用户模块开始，预计 Q2 完成"

run_test "T3" "stress test my plan" "yes" \
  "stress test my plan: 我要在一周内独立完成一个全栈 SaaS 产品 MVP，技术栈是 Next.js + Supabase"

run_test "T4" "中文：对齐一下想法" "yes" \
  "对齐一下想法：我想把团队的部署流程改成 GitOps，用 ArgoCD 管理 K8s 集群"

run_test "T5" "review my design (设计评审场景)" "yes" \
  "review my design: 我设计了一个事件驱动的通知系统，用 Kafka 做消息队列，消费者是多个微服务"

run_test "T6" "有初步方案需要被挑战" "yes" \
  "我有个初步方案但需要被挑战一下：打算用 NoSQL 存所有数据，包括财务报表和用户关系"

# --- Should NOT TRIGGER ---
run_test "T7" "普通编程问题" "no" \
  "帮我写一个 Python 快速排序函数"

run_test "T8" "代码调试" "no" \
  "我的 Node.js 应用报错：Cannot read property of undefined，帮我调试一下"

run_test "T9" "解释代码" "no" \
  "解释一下这段 React useEffect 的代码为什么会导致死循环"

run_test "T10" "文档查询" "no" \
  "Kubernetes 的 Pod 和 Deployment 有什么区别？"

run_test "T11" "生成内容" "no" \
  "帮我写一份 README，项目是一个命令行 JSON 格式化工具"

echo ""
echo "============================================"
echo "  评测结果汇总"
echo "============================================"
echo "总计: $TOTAL  通过: $PASS  失败: $FAIL"
echo "准确率: $(echo "scale=1; $PASS * 100 / $TOTAL" | bc)%"
echo "============================================"
