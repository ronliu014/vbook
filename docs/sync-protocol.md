# vBook Sync 协议规划

## 目的

`sync/` 是 wcodex 与 lcodex 之间的 Git 文件信箱，用于规划、handoff、审查和状态同步。它不是业务数据通道，不能承载视频、模型、抽帧图片或大型输出。

## 角色

- `wcodex`：Windows 端 Codex。
- `lcodex`：Linux 端 Codex。

## 目标目录结构

```text
sync/
|-- PROTOCOL.md
|-- w2l/
|   +-- <seq>-<ts>-<id>.md
|-- l2w/
|   +-- <seq>-<ts>-<id>.md
|-- state/
|   |-- wcodex.json
|   +-- lcodex.json
|-- shared/
|   +-- decisions.md
+-- examples/
```

当前仓库已有 `sync/inbox`、`sync/outbox` 和 `sync/shared`。本文先定义目标协议，后续再迁移目录。

## 单写者规则

每个路径只允许一个写入者：

- `sync/w2l/` 只允许 `wcodex` 新增文件。
- `sync/l2w/` 只允许 `lcodex` 新增文件。
- `sync/state/wcodex.json` 只允许 `wcodex` 修改。
- `sync/state/lcodex.json` 只允许 `lcodex` 修改。
- `sync/shared/` 只存放稳定共识，修改时应谨慎。

消息文件只追加。一旦提交，不应修改或删除。

## 文件命名

```text
<seq>-<ts>-<id>.md
```

- `seq`：当前方向内的 6 位递增序号。
- `ts`：UTC 时间戳，例如 `20260625T120000Z`。
- `id`：短随机十六进制标识。

示例：

```text
sync/w2l/000001-20260625T120000Z-a1b2c3d4.md
```

## 消息格式

```markdown
# <subject>

From: wcodex
To: lcodex
Status: request
In-Reply-To:

## Context

相关文件、约束和背景。

## Request

希望接收方执行的具体动作。

## Next

期望的后续反馈或完成信号。
```

## 操作规则

1. 读写 sync 前先执行 `git pull`。
2. 只写发送方拥有的方向目录。
3. 使用清晰提交信息，例如 `sync: w2l architecture review request`。
4. 提交后执行 `git push`。
5. 大文件永远不要进入 `sync/`。

## 迁移说明

在为 sync 增加自动化脚本前，应先把当前脚手架迁移到目标结构，并保留已有 handoff 内容到 `sync/shared/`。
