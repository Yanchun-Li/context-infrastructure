#!/usr/bin/env python3
"""
L1 Observer Agent (Trigger Script)
Hands a self-contained prompt to `claude -p` to scan, filter, and write to memory.
"""
import os
from datetime import datetime
from pathlib import Path
from claude_client import run_claude, DEFAULT_MODEL

WORKSPACE = os.getenv("CLAUDE_PROJECT_ROOT") or str(Path(__file__).resolve().parents[4])
KNOWLEDGE_BASE = os.path.join(WORKSPACE, "periodic_jobs", "ai_heartbeat", "docs", "KNOWLEDGE_BASE.md")
OBSERVATIONS_PATH = os.path.join(WORKSPACE, "contexts", "memory", "OBSERVATIONS.md")
# 观测范围与记忆存储解耦：SCAN_ROOT 只控制扫描哪里，OBSERVATIONS/SOP 始终留在 WORKSPACE。
SCAN_ROOT = os.getenv("OBSERVER_SCAN_ROOT") or WORKSPACE
SESSION_ROOT = os.getenv("OBSERVER_SESSION_ROOT") or str(Path.home() / ".claude" / "projects")

PROMPT_TEMPLATE = """
【目标】：执行观测记忆提取并直接持久化到磁盘。
【基准日期】：{target_date}

【幂等性约束】：在执行任何写入前，**必须先**读取 OBSERVATIONS.md，检查是否已存在 `Date: {target_date}` 的条目。若存在，则**不要进行任何文件修改**，直接回复「Entry for {target_date} already exists, skipping」即可。

【SOP 路径】：
{kb_path}

【任务内容】：
1. **获取 Context**：请阅读上述 SOP 以及其中引用的 L3 约束文件。
2. **幂等性检查**：读取 OBSERVATIONS.md，若已有 `Date: {target_date}` 则跳过后续步骤。
3. **扫描与过滤**：自主扫描观测根目录（{scan_root}）下当日的变动。记忆系统本仓库位于 {workspace}，它也在观测范围内。
4. **Session 观测**：扫描 Claude Code session 目录（{session_root}）中当日有变动的 `.jsonl` 文件（如 `find {session_root} -name "*.jsonl" -mtime -1`）。目录名编码了项目路径（`-Users-xxx-Projects-foo` 对应 `~/Projects/foo`）。这些文件可能有几十 MB，**禁止全文读取**：用 `head`/`tail`/`grep` 抽样用户消息，提炼出"当天在哪些项目上做了什么、做了什么关键决策"作为观测素材。不要把 session 原文大段复制进观测记录。
5. **写入记忆**：将针对 {target_date} 的 🔴 🟡 🟢 观测结果直接写入或追加到 `{observations_path}`。**鼓励使用命令行 append**（如 `echo "..." >> OBSERVATIONS.md` 或 `tee -a`），避免对大文件做全文编辑。
6. **范围约束**：**仅执行 L1 Observer 任务**。不要执行 SOP 中提到的 L2 Reflector 任务（即不要修改 `rules/` 下的任何文件，不要进行规则晋升或垃圾回收）。
7. **格式规范**：
   - 日期 Header 必须严格使用 `Date: YYYY-MM-DD` 格式（Date 首字母大写，冒号后空格，日期为 ISO 格式）。
   - 提到本仓库（{workspace}）内的文件时，使用相对于仓库根的完整路径（例如：`rules/skills/workflow_deep_research_survey.md`）；提到仓库外的文件时，使用相对于 {scan_root} 的路径，以项目目录名开头（例如：`ai-devination/src/main.py`）。不要只写文件名。
8. **汇报**：完成后，在此回复一个简短的 Walkthrough。
"""


def main():
    import argparse
    parser = argparse.ArgumentParser(description='L1 Observer Agent')
    parser.add_argument('date', nargs='?', default=datetime.now().strftime("%Y-%m-%d"),
                        help='Target date (YYYY-MM-DD)')
    parser.add_argument('--model', default=DEFAULT_MODEL,
                        help=f'Claude model id (default: {DEFAULT_MODEL})')
    args = parser.parse_args()

    target_date = args.date
    model_id = args.model

    if os.path.exists(OBSERVATIONS_PATH):
        with open(OBSERVATIONS_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        if f"Date: {target_date}" in content:
            print(f"Idempotent skip: entry for {target_date} already exists in OBSERVATIONS.md")
            return

    print(f"Triggering Fully Agentic Observer for date: {target_date} using model: {model_id}...")
    prompt = PROMPT_TEMPLATE.format(kb_path=KNOWLEDGE_BASE, target_date=target_date,
                                    workspace=WORKSPACE, observations_path=OBSERVATIONS_PATH,
                                    scan_root=SCAN_ROOT, session_root=SESSION_ROOT)
    output = run_claude(prompt, model_id=model_id)
    if output is None:
        print("Observer run failed.")
        return
    print("Observer run complete.")
    if output.strip():
        tail = output.strip().splitlines()[-20:]
        print("--- agent walkthrough (tail) ---")
        print("\n".join(tail))


if __name__ == "__main__":
    main()
