#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai-fit-check — 判断一件事能不能交给 AI 批量做。

只依赖 Python 标准库。输入一份任务清单（JSON），输出每个任务的判定。

用法：
    python audit.py examples/store-inquiry.json
    python audit.py tasks.json --json

判据（三条硬闸门，缺一即不可批量）：
    G1 有唯一正确答案或可核对的对照
    G2 失败可被自动检测（不需要人肉品味判断）
    G3 结果差异不会引出公平感问题（不会变成人与人之间的比较）

另外两条软闸门（影响成本，不影响对错）：
    S1 输入数据可获取（结构化或可稳定抽取）
    S2 人工判断占比 <= 0.2（每一单里需要"人拍板"的比例）

输出四档：BATCH(可批量) / HUMAN_REVIEW(半自动，人审) / NOT_BATCHABLE(不可批量) / BLOCKED(合规或数据前置缺失)
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

GATES = {
    "g1_objective": "G1 有唯一正确答案或可核对的对照",
    "g2_auto_detectable": "G2 失败可被自动检测",
    "g3_no_fairness_comparison": "G3 差异不引发公平感比较",
}
SOFT = {
    "s1_data_available": "S1 输入数据可获取",
    "s2_judgement_share_ok": "S2 人工判断占比 <= 0.2",
}


def evaluate(task: dict[str, Any]) -> dict[str, Any]:
    """对单个任务给出判定。字段缺失按 False 处理（宁可保守）。"""
    name = task.get("name") or "(unnamed)"
    volume = float(task.get("monthly_volume") or 0)      # 每月发生次数
    minutes = float(task.get("minutes_per_case") or 0)   # 每次人工耗时（分钟）
    judgement = float(task.get("human_judgement_share") or 0.0)  # 0~1
    regulatory = bool(task.get("regulated"))

    failed_hard: list[str] = []
    for key, label in GATES.items():
        if not bool(task.get(key)):
            failed_hard.append(label)

    soft_fail: list[str] = []
    if not bool(task.get("s1_data_available")):
        soft_fail.append(SOFT["s1_data_available"])
    if judgement > 0.2:
        soft_fail.append("%s（实测 %.2f）" % (SOFT["s2_judgement_share_ok"], judgement))

    monthly_hours = round(volume * minutes / 60.0, 1)

    if regulatory:
        verdict, reason = "BLOCKED", "涉及需前置资质的业务，自动化前先解决合规问题"
    elif len(failed_hard) >= 1:
        verdict = "NOT_BATCHABLE"
        reason = "硬闸门未过：" + "；".join(failed_hard)
    elif soft_fail:
        verdict = "HUMAN_REVIEW"
        reason = "硬闸门通过，但需人工复核：" + "；".join(soft_fail)
    else:
        verdict = "BATCH"
        reason = "三条硬闸门全部通过，可批量自动化"

    # 粗估：可批量省 80% 工时，半自动省 40%，不可批量省 0
    saved_ratio = {"BATCH": 0.8, "HUMAN_REVIEW": 0.4}.get(verdict, 0.0)
    return {
        "name": name,
        "verdict": verdict,
        "reason": reason,
        "monthly_human_hours": monthly_hours,
        "est_monthly_hours_saved": round(monthly_hours * saved_ratio, 1),
        "hard_gates_failed": failed_hard,
        "soft_gates_flagged": soft_fail,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="判断一件事能不能交给 AI 批量做")
    ap.add_argument("input", help="任务清单 JSON：要么是任务数组，要么是 {tasks: [...]}")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而不是表格")
    args = ap.parse_args(argv)

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    tasks = data.get("tasks", []) if isinstance(data, dict) else data
    if not tasks:
        print("没有任务可评估。", file=sys.stderr)
        return 2

    results = [evaluate(t) for t in tasks]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    order = {"BATCH": 0, "HUMAN_REVIEW": 1, "NOT_BATCHABLE": 2, "BLOCKED": 3}
    results.sort(key=lambda r: (order[r["verdict"]], -r["monthly_human_hours"]))
    width = max(len(r["name"]) for r in results)
    print("%-*s  %-13s  %7s  %7s  %s" % (width, "任务", "判定", "月人工h", "可省h", "原因"))
    print("-" * (width + 62))
    for r in results:
        print("%-*s  %-13s  %7.1f  %7.1f  %s" % (
            width, r["name"], r["verdict"], r["monthly_human_hours"],
            r["est_monthly_hours_saved"], r["reason"]))
    total = sum(r["est_monthly_hours_saved"] for r in results)
    print("-" * (width + 62))
    print("合计可省 %.1f 小时/月（按 80%% 自动化率的上限估计，实际以试点为准）" % total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
