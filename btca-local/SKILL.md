---
name: btca-local
description: 本地 Git 仓库搜索助手。当用户说"use btca"、要求搜索/查阅某个 GitHub 仓库的代码或文档、或需要基于本地已克隆仓库回答技术问题时触发。
---

# BTCA Local

BTCA Local（"The Better Context App Local"）是一个以 skill 文件定义的轻量应用，核心用途是**在本地搜索已克隆的 Git 仓库**，为用户的技术问题提供带引用、带代码示例的高质量回答。

## 搜索工作流

<guidelines>
    <guideline>
        如果用户给出了 GitHub 仓库直链，优先加载并引用该仓库
    </guideline>
    <guideline>
        如果用户没有给出具体链接/仓库，根据上下文尽力推断最相关的仓库
    </guideline>
    <guideline>
        回答中必须包含链接/引用，说明信息来源
    </guideline>
    <guideline>
        代码示例必须完整，包含 import 等必要上下文，不得省略
    </guideline>
    <guideline>
        使用列表（有序/无序）组织回答，保持可读性
    </guideline>
</guidelines>

<workflow>
    <step name="工作目录准备">
        使用 ~/.btca/agent/sandbox 作为克隆/搜索仓库的工作目录
    </step>
    <step name="加载仓库">
        如果目标仓库已在 ~/.btca/agent/sandbox 中，执行 git pull 更新；否则克隆。默认克隆 main 分支，除非用户指定其他分支
    </step>
    <step name="搜索与回答">
        在仓库中搜索所需信息，遵循上述 guidelines 组织回答
    </step>
</workflow>

<end_goal>
清晰、简洁的回答，附带代码示例与引用
</end_goal>

## 启动场景

### 场景一：用户仅触发 skill，无额外问题

这是"应用启动"状态。扫描 ~/.btca/agent/sandbox 顶层目录，列出已克隆的仓库，输出：

```md
# BTCA Local

_使用你的 coding agent 在本地搜索任意 git 仓库_

已搜索过的仓库：

- repo 1
- ...

给我一个问题和 git 仓库链接即可开始！
（也可以清理或预加载资源到列表中……）
```

### 场景二：agent 自行调用（因用户 prompt 需要）

忠实执行用户 prompt，在需要时使用 BTCA 搜索工作流增强回答质量。

### 场景三：用户触发 skill 并附带问题

直接使用 BTCA 搜索工作流回答用户问题。
