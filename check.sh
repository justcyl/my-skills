#!/bin/bash
# check.sh - 检测散落在各处的未纳管 skill
# 用法: ./check.sh        检查差异
#       ./check.sh sync    检查并将新 skill 拷贝到 my-skills

MANAGED_DIR="$(cd "$(dirname "$0")" && pwd)"
WATCH_DIRS=(
    "$HOME/.claude/skills"
    "$HOME/.agents/skills"
    "$HOME/.cc-switch/skills"
    "$HOME/.openclaw/skills"
)

# 别名映射：外部名称=my-skills中的名称
# 同一个 skill 在不同 agent 目录下可能叫不同名字
ALIAS_KEYS=("qwen-asr-skill" "siliconflow-qwen-asr")
ALIAS_VALS=("qwen-asr"       "qwen-asr")

# diff 时排除的目录/文件模式
DIFF_EXCLUDES="--exclude=__pycache__ --exclude=*.pyc --exclude=.DS_Store"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# 别名查找函数
resolve_alias() {
    local name="$1"
    local i
    for i in "${!ALIAS_KEYS[@]}"; do
        if [ "${ALIAS_KEYS[$i]}" = "$name" ]; then
            echo "${ALIAS_VALS[$i]}"
            return
        fi
    done
    echo "$name"
}

# 收集已纳管的 skill 名称
managed=()
for d in "$MANAGED_DIR"/*/; do
    [ -d "$d" ] && managed+=("$(basename "$d")")
done

new_skills=()
modified_skills=()

for watch in "${WATCH_DIRS[@]}"; do
    [ -d "$watch" ] || continue

    for d in "$watch"/*/; do
        [ -d "$d" ] || continue
        name=$(basename "$d")

        # 跳过非 skill 目录（没有 SKILL.md 的容器目录）
        if [ ! -f "$d/SKILL.md" ]; then
            continue
        fi

        # 解析 symlink 到实际路径
        real_path=$(cd "$d" 2>/dev/null && pwd -P)

        # 跳过指向 my-skills 自身的 symlink
        if [[ "$real_path" == "$MANAGED_DIR"* ]]; then
            continue
        fi

        # 解析别名
        managed_name=$(resolve_alias "$name")

        # 检查是否已纳管
        found=0
        for m in "${managed[@]}"; do
            [ "$m" = "$managed_name" ] && found=1 && break
        done

        if [ $found -eq 0 ]; then
            new_skills+=("$name|$watch/$name")
            echo -e "${RED}[NEW]${NC} $name"
            echo -e "      位置: $watch/$name"
        else
            # 已纳管，检查内容是否有差异
            diff_output=$(diff -rq $DIFF_EXCLUDES "$MANAGED_DIR/$managed_name" "$real_path" 2>/dev/null)
            if [ -n "$diff_output" ]; then
                modified_skills+=("$managed_name|$watch/$name")
                if [ "$name" != "$managed_name" ]; then
                    echo -e "${YELLOW}[MODIFIED]${NC} $managed_name (外部名: $name)"
                else
                    echo -e "${YELLOW}[MODIFIED]${NC} $name"
                fi
                echo -e "      位置: $watch/$name"
                echo "$diff_output" | sed 's/^/      /'
            fi
        fi
    done
done

# 汇总
echo ""
echo "─────────────────────────────────"
echo -e "已纳管: ${GREEN}${#managed[@]}${NC} 个 skill"
echo -e "新发现: ${RED}${#new_skills[@]}${NC} 个"
echo -e "有变更: ${YELLOW}${#modified_skills[@]}${NC} 个"

if [ ${#new_skills[@]} -eq 0 ] && [ ${#modified_skills[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ 一切同步，没有遗漏${NC}"
    exit 0
fi

# sync 模式：自动拷贝
if [ "$1" = "sync" ]; then
    echo ""
    for entry in "${new_skills[@]}"; do
        name="${entry%%|*}"
        src="${entry##*|}"
        real_src=$(cd "$src" 2>/dev/null && pwd -P)
        echo -e "${CYAN}[SYNC]${NC} 拷贝新 skill: $name"
        cp -R "$real_src" "$MANAGED_DIR/$name"
    done
    for entry in "${modified_skills[@]}"; do
        managed_name="${entry%%|*}"
        src="${entry##*|}"
        real_src=$(cd "$src" 2>/dev/null && pwd -P)
        echo -e "${CYAN}[SYNC]${NC} 更新已变更 skill: $managed_name"
        rm -rf "$MANAGED_DIR/$managed_name"
        cp -R "$real_src" "$MANAGED_DIR/$managed_name"
    done
    echo -e "${GREEN}✓ 同步完成，请 cd $MANAGED_DIR && git diff 查看变更${NC}"
fi
