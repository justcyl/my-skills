---
name: mole-release-notes
description: 为 tw93/Mole 的 V<version> 标签撰写和发布双语 GitHub Release notes。仅在用户明确要求 Mole 发布说明、release notes、发版文案或发布到 GitHub Release 时使用。默认只起草, 只有用户明确说 publish/发布/提交后才允许调用 gh release edit 和追加 reactions。
disable-model-invocation: true
---

# Mole Release Notes

这个 skill 用于处理 `tw93/Mole` 发版后的 curated release notes。Mole 的 `release.yml` 会在推送 `V*` 标签后创建 GitHub Release 和构建产物, 但 `generate_release_notes: false`, 因此发布说明需要在 workflow 完成后用 `gh release edit` 补上。

核心约束: **只允许编辑已存在的 release, 不允许创建 release**。如果 release 尚不存在, 等待 workflow 完成, 不要运行 `gh release create`。

## 触发条件

使用本 skill 的典型请求:

- “给 Mole V1.40.0 写 release notes”
- “发布 Mole 这次发版说明”
- “整理 tw93/Mole 的双语 changelog”
- “把 Mole release notes 发到 GitHub Release”

如果用户只是顺口提到 release notes, 只起草文案, 不执行发布动作。

## 必要输入

开始起草前确认:

1. **版本号**: 必须是大写 `V`, 例如 `V1.38.0`。小写 `v` 不会触发 Mole 的 release workflow。
2. **CodeName 和 emoji**: 向用户确认。标题格式为 `V<version> <CodeName> <emoji>`。
3. **提交范围**: 用 `git log <previous-tag>..V<version> --oneline` 收集原始变更。
4. **用户可感知变化**: 阅读完整 commit message, 不只看 subject。特别注意检测范围收窄、功能移除、受控回退等内容, 这些需要写入发布说明。
5. **Sponsors**: 在本 skill 目录运行 `scripts/sponsors.sh`。
6. **Contributors**: `git log <previous-tag>..V<version> --pretty='%an' | sort -u`, 排除 `tw93` 和 bot。
7. **Release 已存在**: `gh release view V<version> --repo tw93/Mole --json id,name` 必须返回结果。没有结果时等待, 不创建 release。

## 发布前检查

这些检查通常应在打标签前完成, 发布 notes 前仍要确认:

- `grep '^VERSION=' mole` 与 `<version>` 一致。
- `SECURITY_AUDIT.md` 开头行包含新版本和日期。
- `./scripts/check.sh --format` 通过。
- `MOLE_TEST_NO_AUTH=1 MOLE_TEST_JOBS=2 BATS_FORMATTER=tap ./scripts/test.sh` 通过。
- `go test ./cmd/...` 和 `make build` 通过。

任一失败时停止。先修复 release 状态, 不要急着发布说明。

## 文案格式

严格遵循 Mole V1.37.0 之后的双语结构。拿不准时参考:

```bash
gh release view V1.37.0 --repo tw93/Mole --json body --jq .body
```

模板:

```md
## What's new in V<version> <emoji>

1. **<English headline>**: <one-sentence English elaboration>.
2. ...

## V<version> 更新内容 <emoji>

1. **<中文 headline>**：<一句中文说明>。
2. ...

## Thanks 💖

Sponsors: <@handle1> <@handle2> ...
Contributors: <@handle1> <@handle2> ...

> Mole · macOS cleanup · https://github.com/tw93/Mole
```

格式规则:

- 不使用 em dash。用逗号、句号、冒号、分号或括号。
- 除两个版本标题里的版本 emoji 和 `Thanks 💖` 外, 不添加其他 emoji。
- 不在条目内写 PR 编号或 `@handle` 致谢, 统一放到 Thanks 区块。
- 英文在前, 中文在后。两段条目顺序和数量必须一致。
- 按用户感知影响排序, 不按提交时间排序。
- 发布说明里提到的命令必须在 HEAD 中真实存在。
- 图标选择要避免误导。不要用表示“清理安全”的图标描述需要用户审查的项目。

## 发布流程

用户确认草稿并明确要求发布后, 才运行:

```bash
gh release edit V<version> --repo tw93/Mole \
  --title "V<version> <CodeName> <emoji>" \
  --notes-file <path-to-draft>
```

随后追加标准 reactions:

```bash
bash scripts/post-reactions.sh V<version>
```

发布后可运行:

```bash
gh release view V<version> --repo tw93/Mole --web
```

提醒用户: Homebrew tap 和 Homebrew core PR 由 workflow 驱动, 除非 workflow 日志显示失败, 不要手动重跑。

## 不要执行的情况

- 用户没有明确给出 publish/发布/提交信号时, 只输出草稿。
- `gh release view` 找不到 release 时, 等 workflow 完成。
- 不运行 `gh release create`。
- 不读取或输出本地 token、密钥、私钥。`gh` 认证由本机 CLI 自行处理。

## Helper Scripts

- `scripts/sponsors.sh`: 通过 `gh api graphql` 获取 tw93 最近 30 个 sponsor。查询只返回 sponsor login。
- `scripts/post-reactions.sh <tag>`: 给指定 Mole release 追加 `+1`, `laugh`, `hooray`, `heart`, `rocket`, `eyes` 六个 reactions。

## 审计结论

- 规则扫描状态为 `warned`, 触发原因是文本提到 GitHub token scope。
- 语义审计结论: 未发现恶意 prompt、越权要求或凭据外传流程。脚本只通过已登录的 `gh` 访问 GitHub API, 一个脚本读取公开 sponsor login, 一个脚本对指定 release 追加 reactions。
- 风险边界: `gh release edit` 和 reactions 都会修改公开 GitHub Release 页面, 必须等用户明确批准后执行。
