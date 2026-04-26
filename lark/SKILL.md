---
name: lark
version: 1.0.0
description: "飞书/Lark 全功能 CLI skill，合并 23 个子 skill。覆盖 IM（收发消息/群聊）、日历（日程/会议室）、云文档（Doc/Markdown/XML）、云空间（Drive/上传下载/权限）、多维表格（Base/字段/记录/视图）、电子表格（Sheets）、演示文稿（Slides）、任务（Task/清单）、邮件（Mail）、知识库（Wiki）、通讯录（Contact）、视频会议（VC/纪要）、事件订阅（Event/WebSocket）、OKR、画板（Whiteboard）、妙记（Minutes）、考勤（Attendance）、审批（Approval）及会议纪要/早报工作流。配合 lark-cli 命令行工具使用，需先完成 config init 和 auth login。"
metadata:
  requires:
    bins: ["lark-cli"]
---

# lark-cli 全功能指南

> 本 skill 合并了全部 23 个飞书子 skill，统一入口。
> 使用前必须先完成 **配置初始化** 和 **认证**（见 § 0）。

---

## § 0. 共享基础（所有域通用）

### 配置初始化

首次使用需运行 `lark-cli config init` 完成应用配置。

以 background 方式发起配置，读取输出中的授权链接发给用户：

```bash
# 发起配置（阻塞直到用户打开链接并完成操作或过期）
lark-cli config init --new
```

### 身份类型

两种身份类型，通过 `--as` 切换：

| 身份 | 标识 | 获取方式 | 适用场景 |
|------|------|---------|---------|
| user 用户身份 | `--as user` | `lark-cli auth login` | 访问用户自己的资源（日历、云空间等） |
| bot 应用身份 | `--as bot` | 自动，只需 appId + appSecret | 应用级操作，访问 bot 自己的资源 |

身份选择原则：
- **Bot 看不到用户资源**：无法访问用户的日历、云空间文档、邮箱等个人资源
- **Bot 无法代表用户操作**：发消息以应用名义发送，创建文档归属 bot
- **Bot 权限**：只需在飞书开发者后台开通 scope，无需 `auth login`
- **User 权限**：后台开通 scope + 用户通过 `auth login` 授权，两层都要满足

### 权限不足处理

错误响应关键字段：`permission_violations`（缺失 scope）、`console_url`（后台链接）、`hint`（修复命令）

**Bot 身份**：将 `console_url` 发给用户去后台开通 scope。禁止对 bot 执行 `auth login`。

**User 身份**：
```bash
lark-cli auth login --domain <domain>           # 按业务域授权
lark-cli auth login --scope "<missing_scope>"   # 按具体 scope 授权（推荐）
```

> `auth login` 必须指定范围（`--domain` 或 `--scope`）。多次 login 的 scope 会累积（增量授权）。

**Agent 代理认证（推荐）**：以 background 方式执行，将授权链接发给用户：
```bash
lark-cli auth login --scope "calendar:calendar:readonly"
```

### 更新检查

命令执行后，如输出包含 `_notice.update` 字段，完成当前请求后提议更新：
```bash
npm update -g @larksuite/cli && npx skills add larksuite/cli -g -y
```
更新完成后提醒用户退出并重新打开 AI Agent 以加载最新 Skills。

### 安全规则

- **禁止输出密钥**（appSecret、accessToken）到终端明文
- **写入/删除操作前必须确认用户意图**
- 用 `--dry-run` 预览危险请求

---

## § 1. 域路由总表

| 域 | 触发场景 | CLI 入口 | 详细节 |
|----|---------|---------|------|
| [§ 2 IM](#-2-消息-im) | 发消息、群聊、聊天记录、下载图片/文件 | `lark-cli im` | — |
| [§ 3 Calendar](#-3-日历-calendar) | 日程、会议预约、会议室、空闲时段 | `lark-cli calendar` | — |
| [§ 4 Doc](#-4-云文档-doc) | 创建/读取/更新飞书文档 | `lark-cli docs` | — |
| [§ 5 Drive](#-5-云空间-drive) | 上传/下载/搜索文件、权限、评论 | `lark-cli drive` | — |
| [§ 6 Base](#-6-多维表格-base) | 多维表格表结构、记录、视图、dashboard | `lark-cli base` | 94 refs |
| [§ 7 Sheets](#-7-电子表格-sheets) | 电子表格读写、查找、导出 | `lark-cli sheets` | 39 refs |
| [§ 8 Slides](#-8-演示文稿-slides) | 幻灯片创建/编辑 | `lark-cli slides` | — |
| [§ 9 Task](#-9-任务-task) | 任务、清单、子任务、提醒 | `lark-cli task` | — |
| [§ 10 Mail](#-10-邮件-mail) | 邮件收发、草稿、监听 | `lark-cli mail` | — |
| [§ 11 Wiki](#-11-知识库-wiki) | 知识空间、节点、成员 | `lark-cli wiki` | — |
| [§ 12 Contact](#-12-通讯录-contact) | 搜索用户、获取 open_id | `lark-cli contact` | — |
| [§ 13 VC](#-13-视频会议-vc) | 会议记录、纪要、逐字稿 | `lark-cli vc` | — |
| [§ 14 Event](#-14-事件订阅-event) | WebSocket 实时事件订阅 | `lark-cli event` | — |
| [§ 15 OKR](#-15-okr) | OKR 周期、目标、关键结果 | `lark-cli okr` | — |
| [§ 16 Whiteboard](#-16-画板-whiteboard) | 画板查看/编辑/DSL渲染 | `lark-cli whiteboard` | — |
| [§ 17 Minutes](#-17-妙记-minutes) | 妙记搜索、下载音视频 | `lark-cli minutes` | — |
| [§ 18 Attendance](#-18-考勤-attendance) | 个人考勤打卡记录 | `lark-cli attendance` | — |
| [§ 19 Approval](#-19-审批-approval) | 审批实例、任务管理 | `lark-cli approval` | — |
| [§ 20 OpenAPI Explorer](#-20-openapi-explorer) | 探索未封装的原生 API | `lark-cli api` | — |
| [§ 21 Skill Maker](#-21-自定义-skill-创建) | 创建自定义 lark-cli skill | — | — |
| [§ 22 WF: 会议纪要](#-22-工作流会议纪要汇总) | 汇总一段时间内的会议纪要 | multi | — |
| [§ 23 WF: 早报](#-23-工作流日程待办摘要) | 今日日程 + 待办摘要 | multi | — |

---

## § 2. 消息（IM）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**

### 核心概念

- **Message**：单条消息，`message_id`（om_xxx）。支持类型：text、post、image、file、audio、video、sticker、interactive（card）等
- **Chat**：群聊或 P2P 会话，`chat_id`（oc_xxx）
- **Thread**：消息的回复线程，`thread_id`（om_xxx 或 omt_xxx）

```
Chat (oc_xxx)
├── Message (om_xxx)
│   ├── Thread（回复线程）
│   ├── Reaction（表情）
│   └── Resource（图片/文件/视频/音频）
└── Member（用户/bot）
```

### 身份注意

- `--as user` → `user_access_token`，以授权用户身份操作
- `--as bot` → `tenant_access_token`，以应用 bot 身份操作
- 同一 API 两种身份结果差异大，注意 chat 成员资格、可见范围等

**Bot 身份获取消息时发件人名称可能不解析**：原因是 bot 应用可见范围未覆盖发送者。解决：在开发者后台调整应用可见范围，或改用 `--as user`。

### Shortcuts（推荐优先使用）

`lark-cli im +<verb> [flags]`

| Shortcut | 说明 |
|----------|------|
| [`+chat-create`](references/im/lark-im-chat-create.md) | 创建群聊，邀请成员，设置 bot 管理员 |
| [`+chat-messages-list`](references/im/lark-im-chat-messages-list.md) | 列出群/P2P 消息，支持时间范围/排序/分页 |
| [`+chat-search`](references/im/lark-im-chat-search.md) | 按关键词/成员搜索可见群聊 |
| [`+chat-update`](references/im/lark-im-chat-update.md) | 更新群名称或描述 |
| [`+messages-mget`](references/im/lark-im-messages-mget.md) | 批量获取消息（最多 50 条 om_id） |
| [`+messages-reply`](references/im/lark-im-messages-reply.md) | 回复消息，支持线程回复和富媒体 |
| [`+messages-resources-download`](references/im/lark-im-messages-resources-download.md) | 下载消息中的图片/文件，支持大文件分片（8MB chunks） |
| [`+messages-search`](references/im/lark-im-messages-search.md) | 跨群搜索消息（user only），支持关键词/发件人/时间/附件过滤 |
| [`+messages-send`](references/im/lark-im-messages-send.md) | 发送消息（text/markdown/post/media），支持幂等 key |
| [`+threads-messages-list`](references/im/lark-im-threads-messages-list.md) | 列出线程消息，支持排序/分页 |

### API Resources

```bash
lark-cli schema im.<resource>.<method>    # 必须先查参数结构
lark-cli im <resource> <method> [flags]  # 调用 API
```

| Resource | 方法 | 身份 |
|---------|------|------|
| chats | create/get/link/list/update | bot/user |
| chat.members | bots/create/delete/get | bot/user |
| messages | delete/forward/merge_forward/read_users | bot(后三者仅bot) |
| reactions | batch_query/create/delete/list | bot/user |
| images | create | bot only |
| pins | create/delete/list | bot/user |

### 权限表

| 方法 | scope |
|------|-------|
| chats.create | `im:chat:create` |
| chats.get/link/list | `im:chat:read` |
| chats.update | `im:chat:update` |
| chat.members.bots/get | `im:chat.members:read` |
| chat.members.create/delete | `im:chat.members:write_only` |
| messages.delete/forward/merge_forward | `im:message` |
| messages.read_users | `im:message:readonly` |
| reactions.batch_query/list | `im:message.reactions:read` |
| reactions.create/delete | `im:message.reactions:write_only` |
| images.create | `im:resource` |
| pins.create/delete | `im:message.pins:write_only` |
| pins.list | `im:message.pins:read` |

---

## § 3. 日历（Calendar）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**
**CRITICAL — 所有 Shortcut 执行前，必须先用 Read 工具读取对应说明文档，禁止直接盲目调用。**
**CRITICAL — 涉及【预约日程/会议】或【查询/搜索会议室】→ 第一步必须读 [`references/calendar/lark-calendar-schedule-meeting.md`](references/calendar/lark-calendar-schedule-meeting.md)。**
**CRITICAL — 口语"帮我约个日历"/"查一下今天的日历" → 实际是日程操作，映射为 `+create`/`+agenda`。**
**CRITICAL — 查询过去时间的会议（"昨天的会""上周的会"）→ 优先走 [§ 13 VC](#-13-视频会议-vc) 搜会议记录。查询日历/日程或未来时间安排 → 使用本域。**
**CRITICAL — 删除/修改日程后，二次查询验证需等待至少 2 秒（不要告知用户等待）。**

**时间推断规范**：
- 周一是一周第一天，周日是最后一天
- "今天/明天"时间范围覆盖整天
- 不能预约已完全过去的时间（跨越当前时间的除外）

### 核心概念

- **Calendar**：日程容器。每用户有主日历（primary），也可创建/订阅共享日历
- **Event**：日程。支持单次和重复日程（RFC5545 iCalendar 标准）
- **Instance**：日程的具体时间实例（重复日程展开后每条）
- **Attendee**：参与者（用户/群/会议室/外部邮箱），各有独立 RSVP 状态
- **Room**：会议室（是日程的 resource attendee，不能单独预定）
- **Time Slot**：确定的连续时间段，如 `14:00~15:00`

### 核心场景

#### 预约日程/会议、查询/搜索可用会议室
**阻塞要求：** 有"预约日程/会议"或"查询/搜索可用会议室"意图 → 立即停止，先完整读取 [`references/calendar/lark-calendar-schedule-meeting.md`](references/calendar/lark-calendar-schedule-meeting.md)，未读前禁止执行任何操作。

- 有明确时间 → 先 `+room-find`，再 `+freebusy`
- 时间模糊/无时间 → 先 `+suggestion` 拿候选时间块，再 `+room-find`
- 用户"查会议室"但未提供明确时间 → 禁止直接调用 `+room-find`，必须先 `+suggestion`
- 选定时间/会议室方案前必须展示给用户确认，禁止擅自决定

### Shortcuts

`lark-cli calendar +<verb> [flags]`

| Shortcut | 说明 |
|----------|------|
| [`+agenda`](references/calendar/lark-calendar-agenda.md) | 查看日程安排（默认今天） |
| [`+create`](references/calendar/lark-calendar-create.md) | 创建日程，邀请参会人（ISO 8601 时间） |
| [`+freebusy`](references/calendar/lark-calendar-freebusy.md) | 查询用户主日历忙闲信息和 RSVP 状态 |
| [`+room-find`](references/calendar/lark-calendar-room-find.md) | 针对明确时间块查找可用会议室（无明确时间时禁止直接调用） |
| [`+rsvp`](references/calendar/lark-calendar-rsvp.md) | 回复日程邀请（接受/拒绝/待定） |
| [`+suggestion`](references/calendar/lark-calendar-suggestion.md) | 根据模糊时间/时间范围推荐多个可用时间块 |

### API Resources

```bash
lark-cli schema calendar.<resource>.<method>
lark-cli calendar <resource> <method> [flags]
```

calendars: create/delete/get/list/patch/primary/search
event.attendees: batch_delete/create/list
events: create/delete/get/instance_view/patch/search/share_info
freebusys: list

### 权限表

| scope | 覆盖方法 |
|-------|---------|
| `calendar:calendar:create` | calendars.create |
| `calendar:calendar:delete` | calendars.delete |
| `calendar:calendar:read` | calendars.get/list/patch/primary/search |
| `calendar:calendar:update` | calendars.patch |
| `calendar:calendar.event:create` | events.create |
| `calendar:calendar.event:delete` | events.delete |
| `calendar:calendar.event:read` | events.get/instance_view/search/share_info，event.attendees.list |
| `calendar:calendar.event:update` | events.patch，event.attendees.batch_delete/create |
| `calendar:calendar.free_busy:read` | freebusys.list |

> **注意**：日期/时间戳转换必须调用系统命令（如 `date`），不要心算。

---

## § 4. 云文档（Doc）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**
**⚠️ API 版本：所有 `docs +create`、`docs +fetch`、`docs +update` 必须携带 `--api-version v2`。**
**CRITICAL — 文档中出现 `<sheet>`、`<bitable>`、`<cite file-type="sheets|bitable">` 标签时，必须主动提取 token 并切到对应技能（[§ 7 Sheets](#-7-电子表格-sheets) / [§ 6 Base](#-6-多维表格-base)）下钻读取。**

执行操作前必读：
1. **读取文档（`docs +fetch`）** → 读 [`references/doc/lark-doc-fetch.md`](references/doc/lark-doc-fetch.md)
2. **创建/编辑文档内容** → 读 [`references/doc/lark-doc-xml.md`](references/doc/lark-doc-xml.md)（Markdown 时改读 [`references/doc/lark-doc-md.md`](references/doc/lark-doc-md.md)）；从零创建时加读 [`references/doc/style/lark-doc-create-workflow.md`](references/doc/style/lark-doc-create-workflow.md)；编辑已有时加读 [`references/doc/style/lark-doc-update-workflow.md`](references/doc/style/lark-doc-update-workflow.md)

```bash
# 常用示例
lark-cli docs +fetch  --api-version v2 --doc "文档URL或token"
lark-cli docs +create --api-version v2 --content '<title>标题</title><p>内容</p>'
lark-cli docs +update --api-version v2 --doc "文档URL或token" --command append --content '<p>内容</p>'
```

### 嵌入对象路由

| 标签 | 参数提取 | 目标域 |
|------|---------|-------|
| `<sheet token="..." sheet-id="...">` | token → spreadsheet_token | [§ 7 Sheets](#-7-电子表格-sheets) |
| `<bitable token="..." table-id="...">` | token → app_token | [§ 6 Base](#-6-多维表格-base) |
| `<cite type="doc" file-type="sheets" ...>` | 同 `<sheet>` | [§ 7 Sheets](#-7-电子表格-sheets) |
| `<cite type="doc" file-type="bitable" ...>` | 同 `<bitable>` | [§ 6 Base](#-6-多维表格-base) |
| `<synced_reference src-token="..." src-block-id="...">` | 用 `docs +fetch` 读取 src-token | [§ 4 Doc](#-4-云文档-doc) |

### 下游路由

- 拿到 spreadsheet URL/token → 切 [§ 7 Sheets](#-7-电子表格-sheets)
- 拿到 bitable URL/token → 切 [§ 6 Base](#-6-多维表格-base)
- 搜索云空间文档 → 优先用 [`drive +search`](references/drive/lark-drive-search.md)（[§ 5 Drive](#-5-云空间-drive)）

### Shortcuts

| Shortcut | 说明 |
|----------|------|
| [`+fetch`](references/doc/lark-doc-fetch.md) | 读取文档（支持 simple/with-ids/full，5种局部读取模式） |
| [`+create`](references/doc/lark-doc-create.md) | 创建文档（DocxXML 或 Markdown） |
| [`+update`](references/doc/lark-doc-update.md) | 更新文档（8种指令：str_replace/block_insert_after/overwrite/append 等） |
| [`+media-download`](references/doc/lark-doc-media-download.md) | 下载文档中的图片/文件 |
| [`+media-insert`](references/doc/lark-doc-media-insert.md) | 向文档插入图片/文件 |
| [`+search`](references/doc/lark-doc-search.md) | 搜索云空间文档（**已进入维护期，新场景改用 `drive +search`**） |

---

## § 5. 云空间（Drive）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**
**分流规则：** 把本地文件导入成 Base/多维表格 → `drive +import --type bitable`（先导入，再切 [§ 6 Base](#-6-多维表格-base) 做内部操作）。

### 快速决策

- 搜文档/Wiki/电子表格/多维表格/云空间对象 → `drive +search`（扁平 flag，无需手写 JSON）
- 导入本地 `.xlsx/.csv/.base` 为 Base → `drive +import --type bitable`
- 导入本地 `.md/.docx/.html` 为在线文档 → `drive +import --type docx`
- 导入本地 `.xlsx/.csv` 为电子表格 → `drive +import --type sheet`
- 新建文件夹 → `drive +create-folder`
- 上传到知识库节点下 → `drive +upload --wiki-token <wiki_token>`
- 修改文件标题（docx/sheet/bitable/file/folder/wiki）→ `drive files patch --data '{"new_title":"..."}'`

### Wiki 链接特殊处理

`/wiki/<token>` 背后可能是不同类型文档，不能直接用作 `file_token`：
```bash
# 先查实际类型和真实 token
lark-cli wiki spaces get_node --params '{"token":"<wiki_token>"}'
# 返回 node.obj_type（docx/sheet/bitable/slides 等）和 node.obj_token（真实 token）
```

### Shortcuts

| Shortcut | 说明 |
|----------|------|
| [`+search`](references/drive/lark-drive-search.md) | 搜索云空间对象（支持 --mine/--edited-since/--doc-types 等扁平 flag） |
| [`+upload`](references/drive/lark-drive-upload.md) | 上传文件到云空间 |
| [`+download`](references/drive/lark-drive-download.md) | 下载文件 |
| [`+import`](references/drive/lark-drive-import.md) | 导入本地文件为在线文档（docx/sheet/bitable） |
| [`+export`](references/drive/lark-drive-export.md) | 导出在线文档为本地格式 |
| [`+create-folder`](references/drive/lark-drive-create-folder.md) | 创建文件夹 |
| [`+move`](references/drive/lark-drive-move.md) | 移动文件 |
| [`+delete`](references/drive/lark-drive-delete.md) | 删除文件 |
| [`+add-comment`](references/drive/lark-drive-add-comment.md) | 添加评论（支持 sheet cell 评论） |
| [`+apply-permission`](references/drive/lark-drive-apply-permission.md) | 管理文档权限 |

---

## § 6. 多维表格（Base）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**
**CRITICAL — 执行任何 `base` 命令前必须先读对应命令的 reference 文档，再调用命令。**
**分流规则：** 本地文件导入 Base → 第一步是 `drive +import --type bitable`，导入完成后再用 `base +...` 做内部操作。

### 触发条件

- 操作飞书多维表格 / Base
- 建表/改表/查表/字段管理/记录读写/视图配置
- 公式字段、lookup 字段、派生指标、跨表计算
- 临时统计、聚合分析、比较排序
- Workflow/dashboard/表单/角色权限管理
- 用户给出 `/base/{token}` 或解析为 bitable 的 `/wiki/{token}` 链接

### 模块地图

| 大模块 | 包含能力 | Reference 入口 |
|------|---------|---------------|
| Base 模块 | base-create/get/copy，链接解析 | [`references/base/lark-base-workspace.md`](references/base/lark-base-workspace.md) |
| 表与数据模块 | table/field/record/view | [`references/base/lark-base-table.md`](references/base/lark-base-table.md) + [`lark-base-field.md`](references/base/lark-base-field.md) + [`lark-base-record.md`](references/base/lark-base-record.md) + [`lark-base-view.md`](references/base/lark-base-view.md) |
| 公式/Lookup | 派生字段、条件判断、跨表计算 | [`references/base/formula-field-guide.md`](references/base/formula-field-guide.md) + [`lookup-field-guide.md`](references/base/lookup-field-guide.md) |
| 数据分析 | 一次性筛选/分组/聚合 | [`references/base/lark-base-data-query.md`](references/base/lark-base-data-query.md) |
| Workflow | 自动化流程 | [`references/base/lark-base-workflow.md`](references/base/lark-base-workflow.md) |
| Dashboard | 仪表盘和图表组件 | [`references/base/lark-base-dashboard.md`](references/base/lark-base-dashboard.md) |
| 表单 | 表单和表单题目 | [`references/base/lark-base-form.md`](references/base/lark-base-form.md) |
| 权限与角色 | 高级权限、自定义角色 | [`references/base/lark-base-role-list.md`](references/base/lark-base-role-list.md) |

> **所有 base 命令格式**：`lark-cli base +<verb>`  
> 执行前必须先读对应 reference，禁止直接调用。

```bash
lark-cli schema base.<resource>.<method>   # 查参数结构
lark-cli base <resource> <method> [flags] # 调用 API
```

---

## § 7. 电子表格（Sheets）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**
**CRITICAL — 执行 sheets 命令前必须先读对应 reference 文档。**

> 操作前先用 `lark-cli schema sheets.<resource>.<method>` 查参数结构。

所有 sheets reference 文档在 [`references/sheets/`](references/sheets/)，按功能分类：
- **基本操作**：create/get/update/append/find — 查 `lark-cli sheets --help`
- **导出**：`+export-csv`、`+export-xlsx`
- **数据类型**：`references/sheets/` 下各 `.md` 文件

```bash
lark-cli schema sheets.<resource>.<method>
lark-cli sheets <resource> <method> [flags]
```

---

## § 8. 演示文稿（Slides）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**

### Shortcuts

| Shortcut | 说明 |
|----------|------|
| [`+create`](references/slides/lark-slides-create.md) | 创建演示文稿 |
| [`+fetch`](references/slides/lark-slides-fetch.md) | 读取演示文稿内容 |
| [`+add-slide`](references/slides/lark-slides-add-slide.md) | 添加幻灯片页 |
| [`+delete-slide`](references/slides/lark-slides-delete-slide.md) | 删除幻灯片页 |
| [`+replace-slide`](references/slides/lark-slides-replace-slide.md) | 块级 XML 编辑（block_replace/block_insert） |

> 所有 slides reference 文档在 [`references/slides/`](references/slides/)。  
> 使用 `+replace-slide` 前必须读 [`references/slides/lark-slides-replace-slide.md`](references/slides/lark-slides-replace-slide.md)。

```bash
lark-cli schema slides.<resource>.<method>
lark-cli slides <resource> <method> [flags]
```

---

## § 9. 任务（Task）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**

**搜索 vs 列取决策**：
- 有明确查询关键字 → `+search`
- 无关键字，只有范围条件（"我关注的/由我创建/分配给我"）→ 优先 `+get-related-tasks` 或 `+get-my-tasks`
- 不要把时间范围词（"今年以来"）误当 `query` 参数
- 用户提到"todo"（待办）→ 优先理解为 task

**创建/更新注意**：
1. 设置 `repeat_rule` 或 `reminder` 之前必须先设置 `due`
2. 同时设置 `start` 和 `due` 时，开始时间 ≤ 截止时间
3. bot 身份无法跨租户添加任务成员

**Task GUID**：API 中的 `guid` 是全局唯一标识，不是客户端展示的任务编号（`t104121`）。从 applink 取 `guid` 参数。

**输出要求**：同时输出任务的 `url` 字段，便于用户点击跳转。

### Shortcuts

`lark-cli task +<verb> [flags]`

| Shortcut | 说明 |
|----------|------|
| [`+create`](references/task/lark-task-create.md) | 创建任务 |
| [`+update`](references/task/lark-task-update.md) | 更新任务 |
| [`+complete`](references/task/lark-task-complete.md) | 完成任务 |
| [`+reopen`](references/task/lark-task-reopen.md) | 重新打开任务 |
| [`+assign`](references/task/lark-task-assign.md) | 分配/移除任务成员 |
| [`+comment`](references/task/lark-task-comment.md) | 添加评论 |
| [`+get-my-tasks`](references/task/lark-task-get-my-tasks.md) | 列出分配给我的任务 |
| [`+get-related-tasks`](references/task/lark-task-get-related-tasks.md) | 列出与我相关的任务 |
| [`+search`](references/task/lark-task-search.md) | 搜索任务（有关键字时用） |
| [`+tasklist-create`](references/task/lark-task-tasklist-create.md) | 创建清单并批量添加任务 |
| [`+tasklist-search`](references/task/lark-task-tasklist-search.md) | 搜索清单 |
| [`+tasklist-task-add`](references/task/lark-task-tasklist-task-add.md) | 将任务加入清单 |
| [`+tasklist-members`](references/task/lark-task-tasklist-members.md) | 管理清单成员 |
| [`+set-ancestor`](references/task/lark-task-set-ancestor.md) | 设置/清除父任务 |
| [`+reminder`](references/task/lark-task-reminder.md) | 管理任务提醒 |
| [`+followers`](references/task/lark-task-followers.md) | 管理任务关注者 |
| [`+subscribe-event`](references/task/lark-task-subscribe-event.md) | 订阅任务事件 |

### 权限表（部分）

| 方法 | scope |
|------|-------|
| tasks CRUD | `task:task:write` / `task:task:read` |
| tasklists CRUD | `task:tasklist:write` / `task:tasklist:read` |
| subtasks CRUD | `task:task:write` / `task:task:read` |
| custom_fields | `task:custom_field:write` / `task:custom_field:read` |

---

## § 10. 邮件（Mail）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**

> 所有 mail reference 文档在 [`references/mail/`](references/mail/)，执行对应操作前先读相应文档。

```bash
lark-cli schema mail.<resource>.<method>
lark-cli mail <resource> <method> [flags]
```

| 功能类别 | 相关 Reference |
|---------|--------------|
| 邮件列表/搜索/读取 | `references/mail/` 下对应文档 |
| 发送/回复/转发 | 同上 |
| 草稿管理 | 同上 |
| 监听新邮件 | 同上 |
| 邮件分享到 IM | [`references/mail/lark-mail-share-to-chat.md`](references/mail/lark-mail-share-to-chat.md) |

---

## § 11. 知识库（Wiki）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**

**成员管理限制**：
- `--as bot` + 部门 → **不支持**，直接说明路径不可行，不要试错
- bot 路径无法完成时不要静默切换到 user；若用户明确要求 bot，必须说明无法完成

**快速决策**：
- 用户给 wiki URL（`.../wiki/<token>`），后续要查/加/删成员 → 先 `wiki spaces get_node` 获取 `space_id`
- 删除知识空间只有名称/URL → 必须先解析出真实 `space_id`，展示候选让用户确认后再执行
- 命中 0 条 → 停下询问，不要改名重试
- "我的文档库/My Document Library/个人知识库" → Wiki personal library，不是 Drive 根目录

**成员添加流程**：先把"人/群/部门"解析成正确 `member_id` 再调用：
- 用户 → `contact +search-user` 获取 `open_id`（`member_type=openid`）
- 群 → `im +chat-search` 获取 `chat_id`（`member_type=openchat`）
- 部门（user 身份）→ 搜索 `open_department_id`（`member_type=opendepartmentid`）

### Shortcuts

| Shortcut | 说明 |
|----------|------|
| [`+move`](references/wiki/lark-wiki-move.md) | 移动 wiki 节点，或将 Drive 文档移入 Wiki |
| [`+node-create`](references/wiki/lark-wiki-node-create.md) | 创建 wiki 节点（自动解析 space） |
| [`+delete-space`](references/wiki/lark-wiki-delete-space.md) | 删除知识空间（高风险，需显式 `--yes`） |

### API Resources

spaces: create/get/get_node/list
members: create/delete/list
nodes: copy/create/list

### 权限表

| 方法 | scope |
|------|-------|
| spaces.create | `wiki:space:write_only` |
| spaces.get/list | `wiki:space:read` / `wiki:space:retrieve` |
| spaces.get_node | `wiki:node:read` |
| members.create | `wiki:member:create` |
| members.delete | `wiki:member:update` |
| members.list | `wiki:member:retrieve` |
| nodes.copy | `wiki:node:copy` |
| nodes.create | `wiki:node:create` |
| nodes.list | `wiki:node:retrieve` |

---

## § 12. 通讯录（Contact）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**

### Shortcuts

| Shortcut | 说明 |
|----------|------|
| [`+search-user`](references/contact/lark-contact-search-user.md) | 按姓名/邮箱/手机号搜索用户（按相关性排序） |
| [`+get-user`](references/contact/lark-contact-get-user.md) | 获取用户信息（省略 user_id 则查自己） |

---

## § 13. 视频会议（VC）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**

**路由规则**：
- 查询**已结束**的会议（历史日期/昨天/上周/今天已开的会）→ 使用本域
- 查询**未来**的会议日程/日历 → 使用 [§ 3 Calendar](#-3-日历-calendar)

### 核心概念

- **Meeting**：视频会议实例，`meeting_id` 标识
- **Note**：会议纪要，含 AI 总结、待办、章节（`note_doc_token`）
- **VerbatimDoc**：逐字稿，含说话人和时间戳（`verbatim_doc_token`）
- **MeetingNotes**：用户绑定的纪要文档（`meeting_notes`，仅 `--calendar-event-ids` 路径返回）
- **Minutes**：来自录制产物的妙记，`minute_token` 标识 → 详见 [§ 17 Minutes](#-17-妙记-minutes)

### 核心场景

**搜索会议记录**：仅支持已结束会议，支持关键词/时间段/参与人/组织者/会议室筛选，注意分页。

**整理会议纪要**：
- 默认给纪要文档和逐字稿链接即可，无需读取内容
- 用户明确要总结/待办/章节时才读文档
- 读 `note_doc_token` 时，第一个 `<whiteboard>` 标签是封面图，应一并下载展示

```bash
# 读纪要内容
lark-cli docs +fetch --api-version v2 --doc <note_doc_token> --doc-format markdown
# 下载封面图
lark-cli docs +media-download --type whiteboard --token <whiteboard_token> --output ./minutes/<minute_token>/cover
```

> 产物目录规范：同一会议所有下载产物统一放 `./minutes/{minute_token}/`

**用户意图区分**：
- "纪要/总结/纪要内容" → 同时返回 `note_doc_token` + `meeting_notes`（如有）
- "逐字稿/完整记录/谁说了什么" → `verbatim_doc_token`
- 意图不明确 → 展示所有文档链接让用户选择

### Shortcuts

| Shortcut | 说明 |
|----------|------|
| [`+search`](references/vc/lark-vc-search.md) | 搜索会议记录（支持关键词/时间/参与者等） |
| [`+notes`](references/vc/lark-vc-notes.md) | 获取纪要产物（总结/待办/章节/逐字稿） |
| [`+recording`](references/vc/lark-vc-recording.md) | 获取会议录制信息/minute_token |

---

## § 14. 事件订阅（Event）

**前置条件：** 先读 [§ 0 共享基础](#-0-共享基础所有域通用)。

### Shortcuts

| Shortcut | 说明 |
|----------|------|
| [`+subscribe`](references/event/lark-event-subscribe.md) | 通过 WebSocket 长连接订阅飞书事件（只读，NDJSON 输出）；bot only；支持 compact agent 友好格式、正则路由、文件输出 |

---

## § 15. OKR

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**
**强烈建议** 操作 OKR 前先读 [`references/okr/lark-okr-entities.md`](references/okr/lark-okr-entities.md) 了解业务实体。

### Shortcuts

| Shortcut | 说明 |
|----------|------|
| [`+cycle-list`](references/okr/lark-okr-cycle-list.md) | 获取用户的 OKR 周期列表，可按时间筛选 |
| [`+cycle-detail`](references/okr/lark-okr-cycle-detail.md) | 获取特定 OKR 中所有目标和关键结果 |

### 格式说明

- [`ContentBlock 富文本格式`](references/okr/lark-okr-contentblock.md) — Objective/KeyResult/Notes 字段使用的富文本格式

### API Resources

```bash
lark-cli schema okr.<resource>.<method>
lark-cli okr <resource> <method> [flags]
```

alignments: delete/get
categories: list
cycles: list/objectives_position/objectives_weight
cycle.objectives: create/list

> **注意**：`cycles.objectives_position` 必须同时修改当前周期下所有目标的位置，且不允许重叠；`cycles.objectives_weight` 所有权重值之和必须等于 1。

---

## § 16. 画板（Whiteboard）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**

> 用于查看/导出/编辑飞书文档中的画板，支持预览图、原始节点结构、DSL/PlantUML/Mermaid 格式。
> ⚠️ 若 skill 列表中同时存在 `lark-whiteboard-cli`，忽略它，使用本 skill，并提示用户 `npx skills remove lark-whiteboard-cli -g`。

**前置检查**：
```bash
lark-cli --version                                # 确认 lark-cli 可用
npx -y @larksuite/whiteboard-cli@^0.2.10 -v      # 确认 whiteboard-cli 可用
```

### 快速决策

| 需求 | 行动 |
|------|------|
| 查看画板内容/导出图片 | `+query --output_as image` |
| 获取 Mermaid/PlantUML 代码 | `+query --output_as code` |
| 修改节点文字/颜色（简单改动）| `+query --output_as raw` → 改 JSON → `+update --input_format raw` |
| 用户已提供 Mermaid/PlantUML 代码 | `+update --input_format mermaid/plantuml` |
| 绘制复杂图表（架构/流程/组织等）| 进入创作 Workflow |

> **强制规范（通过 stdin 更新）**：数据来源于本地文件时 **必须** 使用 `--source - --input_format <格式>`

### Shortcuts

| Shortcut | 说明 |
|----------|------|
| [`+query`](references/whiteboard/lark-whiteboard-query.md) | 查询画板（导出为图片/代码/原始节点结构） |
| [`+update`](references/whiteboard/lark-whiteboard-update.md) | 更新画板（支持 PlantUML/Mermaid/OpenAPI 原生格式） |

### 获取 board_token

| 用户给了什么 | 如何获取 |
|-------------|---------|
| 直接给了 `wbcnXXX` | 直接使用 |
| 文档 URL，已有画板 | `docs +fetch` → 从 `<whiteboard token="xxx"/>` 提取 |
| 文档 URL，需新建画板 | `docs +update --command append --content '<whiteboard type="blank"></whiteboard>'` → 取 `data.new_blocks[0].block_token` |

---

## § 17. 妙记（Minutes）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**

飞书妙记 URL 格式：`http(s)://<host>/minutes/<minute-token>`

### 核心概念

- **妙记（Minutes）**：视频会议录制产物或用户上传音视频，`minute_token` 标识
- `minute_token`：从 URL 末尾提取，如遇 `?xxx` 参数截取路径最后一段

### 能力边界

| 能力 | 工具 |
|------|------|
| 搜索妙记列表 | `minutes +search` |
| 查看基础信息（标题/封面/时长）| `minutes minutes get` |
| 下载音视频媒体文件 | `minutes +download` |
| 逐字稿/总结/待办/章节（纪要内容）| ⚠️ 不属于本域 → 用 [§ 13 VC](#-13-视频会议-vc) 的 `vc +notes --minute-tokens` |

### 路由规则

- "我的妙记/某关键词/某段时间内的妙记" → `minutes +search`
- 同时提到"会议/开会/某场会" → 优先走 [§ 13 VC](#-13-视频会议-vc) 先定位会议，再通过 `vc +recording` 获取 `minute_token`
- "这个妙记的逐字稿/总结/待办/章节" → `vc +notes --minute-tokens`

### Shortcuts

| Shortcut | 说明 |
|----------|------|
| [`+search`](references/minutes/lark-minutes-search.md) | 按关键词/所有者/参与者/时间范围搜索妙记 |
| [`+download`](references/minutes/lark-minutes-download.md) | 下载妙记音视频文件（`--url-only` 只返回下载链接） |

> 未显式指定路径时，文件默认落到 `./minutes/{minute_token}/<server-filename>`

---

## § 18. 考勤（Attendance）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**

### 默认参数（必须自动填充，禁止询问用户）

| 参数 | 固定值 |
|------|-------|
| `employee_type` | `"employee_no"` |
| `user_ids`（`--data` 中）| `[]`（空数组） |

```bash
lark-cli schema attendance.user_tasks.query   # 查参数结构
lark-cli attendance user_tasks query --data '{"user_ids":[],"...":"..."}'
```

### 权限表

| 方法 | scope |
|------|-------|
| `user_tasks.query` | `attendance:task:readonly` |

---

## § 19. 审批（Approval）

**CRITICAL — 操作前必读 [§ 0 共享基础](#-0-共享基础所有域通用)**

```bash
lark-cli schema approval.<resource>.<method>
lark-cli approval <resource> <method> [flags]
```

### API Resources

instances: get/cancel/cc/initiated
tasks: remind/approve/reject/transfer/query

### 权限表

| 方法 | scope |
|------|-------|
| instances.get/initiated | `approval:instance:read` |
| instances.cancel/cc | `approval:instance:write` |
| tasks.remind/approve/reject/transfer | `approval:task:write` / `approval:instance:write` |
| tasks.query | `approval:task:read` |

---

## § 20. OpenAPI Explorer

**前置条件：** 先读 [§ 0 共享基础](#-0-共享基础所有域通用)。

当现有 skill 或 CLI 已注册命令**无法覆盖**用户需求时，用本域从飞书官方文档库挖掘原生 API。

### 文档库

```
llms.txt                    ← 顶层索引（所有模块文档链接）
  └─ llms-<module>.txt      ← 模块文档（功能概述 + API 文档链接）
       └─ <api-doc>.md      ← 单个 API（方法/路径/参数/响应/错误码）
```

| 品牌 | 入口 |
|------|------|
| 飞书 | `https://open.feishu.cn/llms.txt` |
| Lark | `https://open.larksuite.com/llms.txt` |

### 挖掘流程

**Step 1：确认现有能力不足**
```bash
lark-cli <service> --help   # 检查是否已有对应命令
```
如果已有对应命令或 shortcut → 直接使用，不继续挖掘。

**Step 2：顶层索引定位模块**
用 WebFetch 获取 `llms.txt`，找到相关模块文档链接。

**Step 3：模块文档找 API**
用 WebFetch 获取模块文档，找到相关 API 文档链接。

**Step 4：读取 API 文档**
获取完整的方法、路径、参数、权限信息。

**Step 5：调用 API**
```bash
lark-cli api GET /open-apis/<path> --params '{"key":"value"}'
lark-cli api POST /open-apis/<path> --data '{"key":"value"}'
```

---

## § 21. 自定义 Skill 创建

### CLI 核心能力

```bash
lark-cli <service> <resource> <method>          # 已注册 API
lark-cli <service> +<verb>                      # Shortcut
lark-cli api <METHOD> <path> [--data/--params]  # 任意 OpenAPI
lark-cli schema <service.resource.method>       # 查参数定义
```

优先级：Shortcut > 已注册 API > `api` 裸调。

### 调研 API

```bash
lark-cli <service> --help                                           # 查已有资源和 Shortcut
lark-cli schema <service.resource.method>                           # 查参数
lark-cli api GET /open-apis/vc/v1/rooms --params '{"page_size":"50"}'  # 未注册 API 直接调用
```

未注册 API → 先用 [§ 20 OpenAPI Explorer](#-20-openapi-explorer) 从官方文档挖掘。

### SKILL.md 模板

```markdown
---
name: lark-<name>
version: 1.0.0
description: "..."
metadata:
  requires:
    bins: ["lark-cli"]
  cliHelp: "lark-cli <service> --help"
---

# <name>

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [§ 0 共享基础](../lark/SKILL.md#-0-共享基础所有域通用)**

## Shortcuts
...
```

---

## § 22. 工作流：会议纪要汇总

**仅支持 user 身份。**

```bash
lark-cli auth login --domain vc         # 基础（查询+纪要）
lark-cli auth login --domain vc,drive   # 含读取纪要文档正文/生成文档
```

### 工作流

```
{时间范围} ─► vc +search ──► 会议列表 (meeting_ids)
                   │
                   ▼
               vc +notes ──► 纪要文档 tokens
                   │
                   ▼
               drive metas batch_query 纪要元数据
                   │
                   ▼
               结构化报告
```

### 步骤

**Step 1：确定时间范围**（默认过去 7 天）

> 日期转换必须调用系统命令（如 `date`），不要心算。

"今天"→当天，"这周"→本周一～now，"上周"→上周一～上周日，"这个月"→1日～now

**Step 2：查询会议记录**
```bash
lark-cli vc +search --start "<YYYY-MM-DD>" --end "<YYYY-MM-DD>" --format json --page-size 30
```
- `--end` 包含当天（查"今天"时 start 和 end 都填今天）
- 搜索范围最大 1 个月，更长时拆分多次查询
- 有 `page_token` 时继续翻页，收集所有 `id`（meeting_id）

**Step 3：获取纪要文档**
```bash
lark-cli vc +notes --meeting-ids "<meeting_id1>,<meeting_id2>"
```

**Step 4：获取纪要元数据**
```bash
lark-cli schema drive.metas.batch_query
lark-cli drive metas batch_query ...  # 最多 10 个文档
```

**Step 5：汇总输出**
按时间排序，输出会议标题、时间、参与人、纪要链接，合并同一天的会议。

---

## § 23. 工作流：日程待办摘要

**仅支持 user 身份。**

```bash
lark-cli auth login --domain calendar,task
```

### 工作流

```
{date} ─┬─► calendar +agenda ──► 日程列表
        └─► task +get-my-tasks ──► 未完成待办列表
                    │
                    ▼
              AI 汇总（冲突检测 + 排序）──► 摘要
```

### 步骤

**Step 1：获取日程**
```bash
# 今天（默认）
lark-cli calendar +agenda

# 指定日期（必须 ISO 8601，不支持 "tomorrow" 等自然语言）
lark-cli calendar +agenda --start "2026-03-26T00:00:00+08:00" --end "2026-03-26T23:59:59+08:00"
```
> `--start`/`--end` 只支持 ISO 8601 或 Unix timestamp，不支持 `"tomorrow"`，需 AI 根据当前日期自行计算。

**Step 2：获取未完成待办**
```bash
lark-cli task +get-my-tasks              # 默认最多 20 条
lark-cli task +get-my-tasks --due-end "2026-03-26T23:59:59+08:00"  # 截止时间过滤
```

**Step 3：AI 汇总**
1. 时间戳转本地时区可读时间
2. 冲突检测：同一时间段有多个日程时标注
3. 按时间排序
4. 格式：先日程（含地点/参会人），再待办（含截止时间/优先级）
