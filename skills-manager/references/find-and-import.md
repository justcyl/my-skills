# Find And Import

## Use This Module

当用户要求以下任务时读取本模块：

- 查找可用 skill
- 给定仓库名、URL 或本地路径导入 skill
- 解释一个外部 skill 的用途和用法

## Flow

1. 识别来源类型：
   - GitHub shorthand
   - GitHub URL
   - 本地路径
   - 其他 URL
2. 下载或复制到临时目录，不直接写入仓库
3. 找到有效 `SKILL.md`
4. 运行风险筛查
5. 写入 `upstream/`
6. 基于 upstream 生成中文优化版 `managed/`
7. 生成简短报告：
   - 技能做什么
   - 核心原理
   - 如何触发
   - 风险摘要
8. 询问是否分发
9. 询问是否提交并推送

## Search Guidance

如果用户先问“有没有 skill 能做 X”，先给候选，再在确认后导入。

优先引用已知 skill 生态来源，不要直接假设用户要导入第一个搜索结果。
