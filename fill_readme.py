"""Write the real results from results/results.jsonl into README.md.

Run after run_eval.py and analyze.py:
    python fill_readme.py
"""

import json
import re
from pathlib import Path

import pandas as pd


def main():
    df = pd.read_json("results/results.jsonl", lines=True)
    df["full"] = df["outcome"] == "full_leak"
    df["any"] = df["outcome"].isin(["full_leak", "partial_leak"])
    model = df["model"].iloc[0]

    overall = df.groupby("defense")[["full", "any"]].mean().mul(100).round(1)
    counts = df.groupby("defense").size()
    by_cat = df.pivot_table(index="category", columns="defense", values="any", aggfunc="mean").mul(100).round(1)
    by_attack = df.pivot_table(index="attack_id", columns="defense", values="any", aggfunc="mean").mul(100).round(1)

    rows = "\n".join(
        f"| {d} | {overall.loc[d, 'full']}% | {overall.loc[d, 'any']}% | {counts[d]} |"
        for d in overall.index
    )
    table = "| Defense | Full leak % | Any leak % | n |\n|---|---|---|---|\n" + rows

    findings = []
    if "baseline" in by_cat.columns:
        top = by_cat["baseline"].sort_values(ascending=False)
        findings.append(
            f"- Most effective attack category against the baseline prompt: **{top.index[0]}** "
            f"({top.iloc[0]}% of responses leaked all or part of the secret)."
        )
        least = top.sort_values().index[0]
        findings.append(f"- Least effective category: **{least}** ({top[least]}%).")
    if {"baseline", "hardened"} <= set(overall.index):
        b, h = overall.loc["baseline", "any"], overall.loc["hardened", "any"]
        change = round(b - h, 1)
        findings.append(
            f"- The hardened system prompt changed the overall leak rate from {b}% to {h}% "
            f"({'a drop' if change >= 0 else 'an increase'} of {abs(change)} percentage points)."
        )
        if "hardened" in by_attack.columns:
            still = by_attack["hardened"].sort_values(ascending=False)
            still = still[still > 0].head(3)
            if len(still):
                names = ", ".join(f"`{a}` ({v}%)" for a, v in still.items())
                findings.append(f"- Attacks that still worked against the hardened prompt: {names}.")
    leak = df[df["outcome"] == "full_leak"].head(1)
    if len(leak):
        r = leak.iloc[0]
        snippet = r["response"].replace("\n", " ")[:220]
        findings.append(
            f"- Example leak ({r['defense']} prompt, attack `{r['attack_id']}`): \"{snippet}\""
        )

    readme = Path("README.md").read_text(encoding="utf-8")
    readme = re.sub(r"Model: `[^`]*`", f"Model: `{model}`", readme, count=1)
    readme = re.sub(
        r"\| Defense \| Full leak % \| Any leak % \| n \|\n\|---\|---\|---\|---\|\n(?:\|.*\|\n?)+",
        table + "\n",
        readme,
        count=1,
    )
    readme = re.sub(
        r"### Key findings\n\n.*?(?=\n## Limitations)",
        "### Key findings\n\n" + "\n".join(findings) + "\n",
        readme,
        count=1,
        flags=re.S,
    )
    Path("README.md").write_text(readme, encoding="utf-8")
    print("README.md updated with real results:")
    print(table)
    print("\n".join(findings))


if __name__ == "__main__":
    main()
