#!/usr/bin/env python3
"""
L2 Reflector Agent (Trigger Script)
Hands a self-contained prompt to `claude -p` to perform memory garbage collection.
"""
import os
from datetime import datetime
from pathlib import Path
from claude_client import run_claude, DEFAULT_MODEL

WORKSPACE = os.getenv("CLAUDE_PROJECT_ROOT") or str(Path(__file__).resolve().parents[4])
KNOWLEDGE_BASE = os.path.join(WORKSPACE, "periodic_jobs", "ai_heartbeat", "docs", "KNOWLEDGE_BASE.md")

PROMPT_TEMPLATE = """
执行记忆系统的"反思与晋升"任务。

SOP: {kb_path}

步骤：
1. 读取 {workspace}/contexts/memory/OBSERVATIONS.md，分析 🔴 和高优 🟡 条目
2. 将具有普适性的内容晋升到 rules/，按职责边界分类：
   - SOUL.md: Agent 身份与核心价值观
   - USER.md: 用户画像与人生哲学
   - COMMUNICATION.md: 沟通风格（仅限沟通，不含技术知识）
   - WORKSPACE.md: 目录路由
   - skills/: 技术方法论、工作流、最佳实践
3. GC：重写 OBSERVATIONS.md，删除已晋升及过期 🟢 记录

晋升门槛：跨项目通用 + 多次验证 + 有明确适用场景
完成后回复简短晋升汇报。
"""


def main():
    import argparse
    parser = argparse.ArgumentParser(description='L2 Reflector Agent')
    parser.add_argument('--model', default=DEFAULT_MODEL,
                        help=f'Claude model id (default: {DEFAULT_MODEL})')
    args = parser.parse_args()

    model_id = args.model
    target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"Triggering Fully Agentic Reflector ({target_date}) using model: {model_id}...")
    prompt = PROMPT_TEMPLATE.format(kb_path=KNOWLEDGE_BASE, workspace=WORKSPACE)
    output = run_claude(prompt, model_id=model_id)
    if output is None:
        print("Reflector run failed.")
        return
    print("Reflector run complete.")
    if output.strip():
        tail = output.strip().splitlines()[-20:]
        print("--- promotion report (tail) ---")
        print("\n".join(tail))


if __name__ == "__main__":
    main()
