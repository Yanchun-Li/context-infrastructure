# 定时任务补跑与幂等性配套设计

## 元数据

- **类型**: BestPractice
- **适用场景**: 设计或修改任何定时/周期任务的调度配置时(launchd、cron、systemd timer、CI schedule 等)
- **创建日期**: 2026-07-06(由 OBSERVATIONS.md 2026-07-03 观测晋升)

## 核心规律

补跑策略必须与任务自身的幂等性设计配套。"错过就补跑"(launchd 的 `RunAtLoad`、systemd timer 的 `Persistent=true`、cron 的 `@reboot`、anacron)对使用者是一个诱人的默认开关,但它安全的前提是任务重复执行不产生副作用。

判断规则:

1. **任务幂等**(有按日期/按 key 的已执行检查,重复跑会自动跳过或产出相同结果)→ 可以开启补跑,漏跑后自动恢复。
2. **任务非幂等**(会追加、重写或发送,重复跑会造成重复副作用)→ 禁用补跑;若确实需要补跑能力,先给任务加幂等保护,再开开关。

补跑开关和幂等保护是同一个设计决策的两半,只改其中一个就是引入 bug。

## 实例

本仓库 ai_heartbeat 的两个 launchd plist 是一对对照:

- `periodic_jobs/ai_heartbeat/launchd/com.s30000.context-infra.observer.plist`:observer 对 `OBSERVATIONS.md` 有按日期的幂等检查(当日已写则跳过),因此开启 `RunAtLoad`,睡眠/关机错过后登录即补跑。
- `periodic_jobs/ai_heartbeat/launchd/com.s30000.context-infra.reflector.plist`:reflector 会重写记忆文件且无幂等保护,重复执行会叠加改写,因此禁用 `RunAtLoad`,只按每周一固定时刻触发。

## 验收标准

新增或修改一个定时任务的调度配置时,以下两问都有明确答案才算完成:

- 这个任务重复执行一次,产物和副作用是否与执行一次完全相同?依据是什么(指向代码里的幂等检查)?
- 补跑开关的取值是否与上一问的答案一致?

## 边界

- 本 skill 只管"补跑开关与幂等性的配套关系",不规定具体调度器的选型或语法。
- 幂等保护的实现方式(日期戳、lock 文件、数据库 unique key)由任务自身决定,这里只要求它存在且可被指认。
