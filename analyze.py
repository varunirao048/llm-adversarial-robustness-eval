"""Summarize results: leak rates by defense and attack category, plus a chart."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results/results.jsonl")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()

    df = pd.read_json(args.results, lines=True)
    df["full_leak"] = df["outcome"] == "full_leak"
    df["any_leak"] = df["outcome"].isin(["full_leak", "partial_leak"])
    outdir = Path(args.outdir)

    overall = (
        df.groupby("defense")[["full_leak", "any_leak"]].mean().mul(100).round(1)
        .rename(columns={"full_leak": "full_leak_%", "any_leak": "any_leak_%"})
    )
    overall["n"] = df.groupby("defense").size()
    by_cat = (
        df.pivot_table(index="category", columns="defense", values="any_leak", aggfunc="mean")
        .mul(100).round(1)
    )
    by_attack = (
        df.pivot_table(index="attack_id", columns="defense", values="any_leak", aggfunc="mean")
        .mul(100).round(1).sort_values(by_cat.columns[0], ascending=False)
    )

    overall.to_csv(outdir / "summary_overall.csv")
    by_cat.to_csv(outdir / "summary_by_category.csv")
    by_attack.to_csv(outdir / "summary_by_attack.csv")

    print(f"Model: {df['model'].iloc[0]}\n")
    print("Overall leak rate (%)\n", overall.to_string(), "\n")
    print("Any-leak rate by attack category (%)\n", by_cat.to_string(), "\n")
    print("Top 5 most effective attacks (%)\n", by_attack.head(5).to_string())

    ax = by_cat.sort_values(by_cat.columns[0]).plot.barh(figsize=(8, 5))
    ax.set_xlabel("Leak rate (%) - full or partial secret revealed")
    ax.set_ylabel("Attack category")
    ax.set_title(f"Secret leakage by attack category\n{df['model'].iloc[0]}")
    ax.set_xlim(0, 100)
    plt.tight_layout()
    plt.savefig(outdir / "leak_rate_by_category.png", dpi=150)
    print(f"\nSaved CSVs and chart to {outdir}/")


if __name__ == "__main__":
    main()
