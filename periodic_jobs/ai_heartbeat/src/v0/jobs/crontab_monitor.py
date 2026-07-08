#!/usr/bin/env python3
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
try:
    from claude_client import run_claude, DEFAULT_MODEL
except ImportError:
    print("Error: Could not import claude_client. Ensure path is correct.")
    sys.exit(1)


def run_ai_analysis(model_id: str = DEFAULT_MODEL):
    """Delegate the entire crontab health check to `claude -p`."""
    prompt = f"""
你是一个系统运维专家，负责维护用户的生产环境。
现在的任务是：**自主完成对系统当前所有 Crontab 任务的健康审计**。

### 核心任务与指导原则：
1. **自主获取数据**：请运行 `crontab -l` 获取所有定时任务。不要依赖我提供的数据，你要自己去实地查看。
2. **深度调查日志**：
   - 对于每个任务，分析其执行频率。
   - 识别日志文件路径。
   - **向下钻取 (Drill-down)**：如果 Crontab 中没有明确的日志重定向（例如没有 `>>`），请**不要直接假设它没有日志**。你应该定位脚本文件（例如 `/path/to/your/workspace/scripts/cron_launcher.sh`）并 `read` 脚本内容，检查其内部是否有日志重定向逻辑（例如 `exec >>`）。
3. **活跃度分析**：
   - 使用工具检查日志文件的最后修改时间。
   - 如果频率很高（如每 2 分钟运行一次），日志应在最近 2 分钟内更新。
   - 如果日志不存在或超过两个周期未更新，视为异常。
4. **报错审计**：
   - `read` 关键日志文件的末尾部分，检查是否有 Python 报错、命令未找到 (command not found) 或网络/DNS 故障。
   - 特别注意 `vatic` 新闻抓取脚本，它的内部日志通常在 `vatic/agentic_trading/runs/news_scraping/cron.log` 或类似位置。

5. **录音质量检查**：
   - 运行 life_record 的录音检查脚本，检查**最近两天**的录音是否有问题。
    - 脚本路径：`/path/to/your/workspace/contexts/life_record/scripts/check_recent_recordings.py`
   - 执行方式：先 `cd /path/to/your/workspace/contexts/life_record`，对最近两天的 YYYYMMDD 各运行一次。可通过 `ls data/` 获取最近两个日期目录，或使用 `date -v-1d +%Y%m%d` 获取昨天日期。示例：`python scripts/check_recent_recordings.py`（最近一天）及 `python scripts/check_recent_recordings.py 20260224`（指定日期）。
   - 关注的问题：覆盖率不足（如 24 小时只录了 2 小时）、音量完全静音（无有效声音）、目录为空等。
   - 若脚本 exit 1 或输出问题描述，视为异常。

### 结果交付逻辑：
- **一切正常**：如果分析结论是所有任务都在按计划运行且无报错，请回复"一切正常，无需介入"，并且**严禁调用邮件工具**。
- **发现异常**：如果发现任何潜在风险或明确故障（包括 Crontab 任务异常或录音质量问题），请调用 `python3 tools/send_email_to_myself.py` 发送报警邮件。
  - **邮件标题**：【告警】Crontab 任务异常审计报告（若有录音问题可加「含录音异常」）
  - **邮件内容**：使用现代美观的 HTML 格式。列出有问题的任务、对应的日志实地路径、具体的报错信息快照；若有录音问题，一并列出日期与问题描述。最后给出专家级修复建议。

请开始你的审计工作。
"""
    print(f"Triggering autonomous crontab audit via claude -p ({datetime.now().strftime('%Y-%m-%d %H:%M')}, model: {model_id})...")
    output = run_claude(prompt, model_id=model_id)
    if output is None:
        print("Autonomous AI Analysis failed.")
        return
    print("Autonomous AI Analysis complete.")
    if output.strip():
        tail = output.strip().splitlines()[-20:]
        print("--- audit summary (tail) ---")
        print("\n".join(tail))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Autonomous Crontab Auditor")
    parser.add_argument("--model", "-M", default=DEFAULT_MODEL,
                        help=f"Claude model id (default: {DEFAULT_MODEL})")
    args = parser.parse_args()
    print("Starting Autonomous Crontab Auditor...")
    run_ai_analysis(model_id=args.model)
    print("Audit process finished.")
