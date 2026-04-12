"""
Pair vs noise permutation audit (SIV aggregate variance).

Compares Var(mean(SIV)) for within-event country pairs vs random row pairs.
Uses benchmark_v2.load_data for TSV schema compatibility.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import permutation_test

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import benchmark_v2 as bv  # noqa: E402

SIV_DIMS = [
    "siv_security",
    "siv_economy",
    "siv_tech",
    "siv_resource",
    "siv_ideology",
    "siv_environment",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Pair vs noise SIV variance permutation test")
    parser.add_argument(
        "--data",
        type=Path,
        default=SCRIPT_DIR.parent / "data" / "narrative_articles.tsv",
        help="TSV path (default: ../data/narrative_articles.tsv)",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-resamples", type=int, default=5000)
    args = parser.parse_args()

    df = bv.load_data(str(args.data))

    pair_entropies: list[float] = []
    noise_entropies: list[float] = []
    rng = np.random.default_rng(args.seed)
    events = [g for _, g in df.groupby("event_id") if len(g) >= 2]

    for grp in events:
        vecs = grp[SIV_DIMS].values
        agg = vecs.mean(axis=0)
        pair_entropies.append(float(np.var(agg)))

    all_vecs = df[SIV_DIMS].values
    for _ in range(len(pair_entropies)):
        idx = rng.choice(len(all_vecs), size=2, replace=False)
        agg = all_vecs[idx].mean(axis=0)
        noise_entropies.append(float(np.var(agg)))

    pair_ent = np.array(pair_entropies)
    noise_ent = np.array(noise_entropies)

    print(f"Pair mean:  {pair_ent.mean():.6f}")
    print(f"Noise mean: {noise_ent.mean():.6f}")
    diff = pair_ent.mean() - noise_ent.mean()
    print(f"Diff (Pair - Noise): {diff:.6f}")
    if diff > 0:
        print("-> Pair > Noise: 激しい衝突フェーズ")
    else:
        print("-> Pair < Noise: 結晶化フェーズ")

    def statistic(x: np.ndarray, y: np.ndarray) -> np.floating:
        return np.mean(x) - np.mean(y)

    res_less = permutation_test(
        (pair_ent, noise_ent), statistic, alternative="less", n_resamples=args.n_resamples
    )
    res_greater = permutation_test(
        (pair_ent, noise_ent), statistic, alternative="greater", n_resamples=args.n_resamples
    )

    print(f"\nP-value (Pair < Noise): {res_less.pvalue:.4f}")
    print(f"P-value (Pair > Noise): {res_greater.pvalue:.4f}")

    print("\n=== Audit Conclusion ===")
    if res_greater.pvalue < 0.05:
        print("Pair > Noise 有意 -> 激しい衝突フェーズ（論文に使える）")
    elif res_less.pvalue < 0.05:
        print("Pair < Noise 有意 -> 結晶化フェーズ（論文に使える）")
    else:
        print("有意差なし -> F4現時点では採用しない")


if __name__ == "__main__":
    main()
