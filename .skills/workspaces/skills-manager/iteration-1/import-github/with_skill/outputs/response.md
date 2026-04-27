全部完成 ✅

---

## 导入汇报

| 项目 | 内容 |
|------|------|
| **skill** | `pdf` |
| **来源** | `anthropics/skills` → `skills/pdf` |
| **受影响文件** | `SKILL.md`、`forms.md`、`reference.md`、`scripts/`（8 个 Python 脚本） |
| **风险审计** | `warned`（扫描器误报：代码示例中的 `"userpassword"` 等占位符触发，非真实凭据）**→ 实际无风险** |
| **中文优化** | 将 `description` 和 Overview 翻译为中文，技术代码保留英文 |
| **分发** | ✅ 已同步 |
| **提交/推送** | ✅ `a040d8c` → `main` |

**典型用法**：当用户提到 `.pdf` 文件操作（提取文字/表格、合并/拆分、填写表单、加密解密、OCR 等）时，此 skill 会被自动触发。填写 PDF 表单时遵循 `forms.md` 中的多步骤流程；高级功能参考 `reference.md`。
Extension error (/opt/homebrew/lib/node_modules/pi-alert/src/alert.ts): This extension ctx is stale after session replacement or reload. Do not use a captured pi or command ctx after ctx.newSession(), ctx.fork(), ctx.switchSession(), or ctx.reload(). For newSession, fork, and switchSession, move post-replacement work into withSession and use the ctx passed to withSession. For reload, do not use the old ctx after await ctx.reload().
Extension error (/Users/chenyl/.pi/agent/git/github.com/justcyl/pi-alert/src/alert.ts): This extension ctx is stale after session replacement or reload. Do not use a captured pi or command ctx after ctx.newSession(), ctx.fork(), ctx.switchSession(), or ctx.reload(). For newSession, fork, and switchSession, move post-replacement work into withSession and use the ctx passed to withSession. For reload, do not use the old ctx after await ctx.reload().
