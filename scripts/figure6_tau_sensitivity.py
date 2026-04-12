"""
Figure 6: Sensitivity analysis of core extraction threshold tau.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mutual_info_score

SCRIPT_DIR = Path(__file__).resolve().parent

parser = argparse.ArgumentParser(description="Figure 6: tau sensitivity (stability vs collision vs retention)")
parser.add_argument(
    "--data",
    type=Path,
    default=SCRIPT_DIR.parent / "data" / "narrative_articles.tsv",
    help="TSV path (default: ../data/narrative_articles.tsv)",
)
parser.add_argument("--lambda-penalty", type=float, default=0.5)
parser.add_argument("--steps", type=int, default=50)
args = parser.parse_args()

df = pd.read_csv(args.data, sep="\t")
print(f"[load] {len(df):,} rows")

SIV_DIMS = ["security", "economy", "tech", "resource", "ideology", "environment"]


def parse_siv(raw):
    try:
        d = json.loads(raw) if isinstance(raw, str) else {}
        return [float(d.get(k, 0.0)) for k in SIV_DIMS]
    except Exception:
        return [0.0] * 6


siv = np.array(df["strategic_interest_vector"].apply(parse_siv).tolist())
for i, dim in enumerate(SIV_DIMS):
    df[f"siv_{dim}"] = siv[:, i]

df["entropy"] = pd.to_numeric(df["entropy"], errors="coerce").fillna(0.5)

NUM_COLS = [f"siv_{d}" for d in SIV_DIMS] + ["entropy"]
ID_COLS = ["country_code"]
print(f"[cols] numeric={len(NUM_COLS)}")

base_labels = pd.factorize(df["event_id"])[0]
TAU_VALUES = np.linspace(0.0, 1.0, args.steps)
stability_list, collision_list, retention_list = [], [], []

num_vals = df[NUM_COLS].values
id_vals = df[ID_COLS].values

for tau in TAU_VALUES:
    hashes = []
    core_labels = []
    for i in range(len(df)):
        core = {}
        for j, col in enumerate(NUM_COLS):
            v = float(num_vals[i, j])
            if abs(v) >= tau:
                core[col] = round(v, 4)
        for j, col in enumerate(ID_COLS):
            core[col] = str(id_vals[i, j])
        jcs = json.dumps(core, sort_keys=True)
        hashes.append(hashlib.sha256(jcs.encode()).hexdigest())
        core_labels.append(hash(jcs) % 100000)

    hash_counts = Counter(hashes)
    unique = sum(1 for c in hash_counts.values() if c == 1)
    stability_list.append(unique / len(hashes))
    dupes = sum(c for c in hash_counts.values() if c > 1)
    collision_list.append(dupes / len(hashes))
    mi = mutual_info_score(base_labels, core_labels)
    max_mi = np.log(max(len(set(base_labels)), 2))
    retention_list.append(min(mi / max_mi, 1.0))

S = np.array(stability_list)
C = np.array(collision_list)
R = np.array(retention_list)

score = R - args.lambda_penalty * C
tau_star_idx = int(np.argmax(score))
tau_star = TAU_VALUES[tau_star_idx]
print(
    f"[result] tau*={tau_star:.4f}  stability={S[tau_star_idx]:.3f}  "
    f"collision={C[tau_star_idx]:.3f}  retention={R[tau_star_idx]:.3f}"
)

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

ax.plot(TAU_VALUES, S, color="#3d5a80", lw=2, label="State hash stability")
ax.plot(TAU_VALUES, C, color="#E24B4A", lw=2, label="Hash collision rate", ls="--")
ax.plot(TAU_VALUES, R, color="#1D9E75", lw=2, label="Information retention")

ax.axvline(tau_star, color="#BA7517", ls=":", lw=1.8)
ax.text(tau_star + 0.02, 0.92, f"tau*={tau_star:.2f}\noptimal", fontsize=10, color="#BA7517")

p_lo = max(0, tau_star_idx - 4)
p_hi = min(len(TAU_VALUES) - 1, tau_star_idx + 4)
ax.axvspan(TAU_VALUES[p_lo], TAU_VALUES[p_hi], alpha=0.08, color="#1D9E75", label="Plateau (robust region)")

ax.annotate("noise regime\n(low tau)", xy=(0.05, 0.45), fontsize=9, color="#aaa", ha="center")
ax.annotate("information\nloss (high tau)", xy=(0.88, 0.45), fontsize=9, color="#aaa", ha="center")

ax.set_xlabel("Threshold tau", fontsize=12)
ax.set_ylabel("Metric value", fontsize=12)
ax.set_title("Figure 6: Sensitivity Analysis of Core Extraction Threshold tau", fontsize=13)
ax.legend(fontsize=10, loc="upper right")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1.05)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
out_png = SCRIPT_DIR / "figure6_tau_sensitivity.png"
plt.savefig(out_png, dpi=150, bbox_inches="tight")
plt.close()
print(f"[saved] {out_png}")
