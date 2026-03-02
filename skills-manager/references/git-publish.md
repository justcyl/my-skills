# Git Publish

## Goal

在确认后将仓库变更提交并推送到当前 GitHub 远端。

## Flow

1. 查看 `git status`
2. 总结当前变更
3. 生成简短 commit message
4. 在确认后执行 `git commit`
5. 在确认后执行 `git push`

## Failure Policy

- commit 失败：停止并报告错误
- push 失败：保留本地提交，不回滚

## Confirmation Boundary

以下动作必须先问用户：

- 是否提交
- 是否推送
