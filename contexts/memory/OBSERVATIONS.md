# Memory Observations

这是三层记忆系统的 L1/L2 层。每日观察由 `periodic_jobs/ai_heartbeat/src/v0/observer.py` 自动写入,每周由 `reflector.py` 整理和蒸馏。

## 格式说明

每个日期条目格式如下：

```
Date: YYYY-MM-DD

🔴 High: [方法论/约束] 描述
🟡 Medium: [项目状态/决策] 描述
🟢 Low: [任务流水] 描述
```

### 优先级定义

- **🔴 High**：跨项目通用的经验教训、硬性约束、影响系统架构的重大决策。永久保留，候选晋升为 axiom 或 skill。
- **🟡 Medium**：活跃项目的关键进展、技术决策背景、未来几周仍需参考的信息。
- **🟢 Low**：日常任务流水、瞬时 debug 记录、临时上下文。定期垃圾回收。

## 如何加载记忆

不要全文加载这个文件（可能很大）。按需检索：

```bash
# 搜索特定主题
grep -n "关键词" contexts/memory/OBSERVATIONS.md

# 搜索最近 N 天
grep -A 20 "Date: $(date -v-7d +%Y-%m-%d)" contexts/memory/OBSERVATIONS.md
```

或使用语义搜索（`rules/skills/semantic_search.md`）做跨日期语义检索。

---

<!-- 以下是记录区域，由 observer.py 自动追加 -->
<!-- Reflector GC 记录: 2026-07-06 —— 2026-07-03 的 🔴 幂等/补跑方法论已晋升至 rules/skills/bestpractice_scheduled_job_idempotency.md;过期 🟢 流水(含 2026-07-02 全部条目)已清理 -->

Date: 2026-07-03

🟡 Medium: [架构迁移] ai_heartbeat 完成从 OpenCode 到 Claude CLI 的运行时迁移：删除 `periodic_jobs/ai_heartbeat/src/v0/opencode_client.py`（-228 行），新增 `periodic_jobs/ai_heartbeat/src/v0/claude_client.py`（`claude -p` 无头调用），`observer.py`、`reflector.py` 及 `jobs/` 下三个任务（`ai_news_survey.py`、`crontab_monitor.py`、`daily_newsletter.py`）全部切换，整体净删约 300 行。
🟡 Medium: [架构变更] 路径解析去硬编码：`periodic_jobs/ai_heartbeat/src/v0/observer.py` 与 `reflector.py` 改为 `CLAUDE_PROJECT_ROOT` 环境变量优先、否则按脚本相对位置推导 workspace 根，替换了原先写死的占位路径，使脚本可移植。
🟡 Medium: [项目状态] 心跳系统调度上线 launchd：observer 每日 08:00（睡眠错过唤醒补跑 + 登录补跑），reflector 每周一 09:00，日志输出至 `/tmp/observer.log` 与 `/tmp/reflector.log`；plist 中直接注入 PATH / CLAUDE_BIN / CLAUDE_PROJECT_ROOT（因 dotenv 未装，`.env` 不会被加载）。

Date: 2026-07-08

🔴 High: [系统可靠性] 2026-07-07 的 Observer 定时任务实际启动过（session `~/.claude/projects/-Users-s30000-Projects-context-infrastructure/8e3870c6-*.jsonl`），但因 `API Error: Connection closed mid-response` 中途死亡，未写入任何 `Date: 2026-07-07` 条目，且无重试或失败告警；本次 07-08 运行仅靠 `find -mtime -1` 窗口顺带补齐了 07-07 的观测。方法论结论：定时任务除幂等（见 rules/skills/bestpractice_scheduled_job_idempotency.md）外，还需要"交付物校验 + 失败重试/告警"——运行结束后检查目标文件是否真的产出了当日条目，否则观测链路会静默断档。
🟡 Medium: [项目进展] ml-face-fraud-detection canary verifier 时序重构落地（commits `8a9a506`/`29488b1`/`38d9738`）：verify 改为「traffic 收集 600s → time.time() snapshot → metric ingestion buffer 300s → 用 snapshot 的 end_time 拉取指标」，新增必须环境变量 `CANARY_METRIC_BUFFER_SECONDS`（缺失即 exit 1 fail-fast）；`canary/metrics.py` 6 个 helper 按 endpoint/service 作用域重命名（如 `get_match_request_count` → `get_endpoint_request_count`），本次仅 stg 生效。
🟡 Medium: [部署约束] canary buffer 变更给 prd 留下一个顺序硬约束：verify 镜像一旦到达 prd 而 prd terraform 尚无 `CANARY_METRIC_BUFFER_SECONDS`，main() 会 exit 1。后续 prd 对应 PR 必须按「先 apply prd terraform → 再 deploy image」的顺序执行（记录于 ml-face-fraud-detection/.relay/tasks/2026-07-07-041224-*/report.md 的 review 结论）。
🟡 Medium: [调研结论] ml-context 数据收集基盘四篇调研定稿（ml-context/docs/research/2026-07-07-*.md）：生数据保存先确定 GCS（东京单 region + UBLA + Hive 前缀直连 BQ 外部表，成本年 $30 以下）；Slack 采集用 bot token 日次轮询 `conversations.history`（bot 邀请列表即 allowlist）；Notion 议事录走官方 Markdown API + Cloud Run Jobs 日次；session 收集统一为各自机器日次 `make collect` + `gcloud storage rsync`，不发 SA key、用 SA impersonation，gitleaks 掩码在本地上传前执行。
🟡 Medium: [项目决策] ml-context 基盘设计会议（2026-07-07，杉山/李/古田，ml-context/docs/meetings/pj-ml-context/2026-07-07-MLコンテキスト基盤設計相談.md）：本阶段只做设计与需求定义、不做实现；最低要件两条——AI 与人都能访问会议/项目 context、个人本地 session 可在团队内共享；争点集中在本地 session 的上传共享架构，蓄积先以 GCS 为第一候选并要求补充对比材料（加密、掩码、GCS vs Git）。
🟡 Medium: [工作流实践] canary verifier 任务通过 relay（cc↔codex 轮替）完成：spec/plan/handoff/review 全链路留档于 ml-face-fraud-detection/.relay/tasks/，两阶段共 4 轮 review 全部 HIGH=0，未触发 fix 循环；用户要求 agent 不做 git 操作、由本人确认后自行 commit。
🟢 Low: [任务流水] ml-context 的 meeting-minutes skill 微调（commit `b5949f4`）：让 ML 能识别「メール」并修正议事录内容（ml-context/skills/meeting-minutes/SKILL.md）。
🟢 Low: [任务流水] ml-context 的 GCS IaC 调研在 session 中继续推进（需要哪些 resource、IaC 需要哪些 roles），文档产出遵循 japanese-tech-docs skill 的「結論 → 根拠」结构。
