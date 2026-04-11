"""
benchmark_v2.py
Narrative Quantification 2.0.1 — Evidence Generation Script
Gemmina Intelligence LLC

Usage:
    # Step 1: Export data from Hostinger (run in terminal, NOT here)
    # See export command at the bottom of this file.

    # Step 2: Run benchmark
    python benchmark_v2.py --data ./data/narrative_articles.tsv

Output:
    evidence_v2_0_1.csv   — raw results for all verifications
    figure3_hazard.png    — Figure 3 inset (hazard function)
    figure4_entropy.png   — Figure 4 (entropy comparison)
    model_comparison.csv  — AIC/BIC table for §8.X.5
"""

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# 0. CONFIG
# ─────────────────────────────────────────────
RANDOM_SEED   = 42
PERM_ITERS    = 1_000          # Figure 4 permutation test
MIN_PAIR_SIZE = 5              # minimum Δt samples per event to include
rng = np.random.default_rng(RANDOM_SEED)


# ─────────────────────────────────────────────
# 1. DATA LOADING
# ─────────────────────────────────────────────
def load_data(path: str) -> pd.DataFrame:
    """
    Load TSV exported from Hostinger.
    Expected columns:
        fact_id, event_id, country_code, created_at,
        state_hash, strategic_interest_vector, audit_aura, entropy
    """
    df = pd.read_csv(path, sep="\t", parse_dates=["created_at"])
    df["entropy"] = pd.to_numeric(df["entropy"], errors="coerce").fillna(0.5)

    # Parse SIV JSON
    import json
    def parse_siv(raw):
        try:
            d = json.loads(raw) if isinstance(raw, str) else {}
            return [float(d.get(k, 0.0)) for k in
                    ["security","economy","tech","resource","ideology","environment"]]
        except Exception:
            return [0.0] * 6

    siv_matrix = np.array(df["strategic_interest_vector"].apply(parse_siv).tolist())
    for i, dim in enumerate(["siv_security","siv_economy","siv_tech",
                              "siv_resource","siv_ideology","siv_environment"]):
        df[dim] = siv_matrix[:, i]

    print(f"[load] {len(df):,} rows, {df['event_id'].nunique():,} events")
    return df


# ─────────────────────────────────────────────
# 2. VERIFICATION 3 — HAZARD FUNCTION & AIC/BIC
# ─────────────────────────────────────────────

def extract_delta_t(df: pd.DataFrame) -> np.ndarray:
    """
    For each event, compute Δt (seconds) between all narrative pairs
    where country_code differs and a < b (ordered).
    """
    deltas = []
    for event_id, grp in df.groupby("event_id"):
        grp = grp.sort_values("created_at").reset_index(drop=True)
        if len(grp) < 2:
            continue
        times = grp["created_at"].values
        codes = grp["country_code"].values
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                if codes[i] != codes[j]:
                    dt = (times[j] - times[i]) / np.timedelta64(1, "s")
                    if dt > 0:
                        deltas.append(dt)
    return np.array(deltas)


def _negloglik_exponential(lam, data):
    if lam <= 0:
        return np.inf
    return -np.sum(stats.expon.logpdf(data, scale=1/lam))


def fit_models(delta_t: np.ndarray) -> pd.DataFrame:
    """
    Fit Exponential, Weibull, Log-Normal to Δt.
    Return AIC/BIC table.
    """
    n = len(delta_t)
    rows = []

    # --- Exponential (k=1 param) ---
    loc_e, scale_e = stats.expon.fit(delta_t, floc=0)
    ll_e = np.sum(stats.expon.logpdf(delta_t, loc=loc_e, scale=scale_e))
    k_e = 1
    rows.append({
        "Model": "Exponential",
        "k": k_e,
        "LogLik": ll_e,
        "AIC": 2*k_e - 2*ll_e,
        "BIC": k_e*np.log(n) - 2*ll_e,
        "Interpretation": "Memoryless (Poisson)"
    })

    # --- Weibull (k=2 params) ---
    c_w, loc_w, scale_w = stats.weibull_min.fit(delta_t, floc=0)
    ll_w = np.sum(stats.weibull_min.logpdf(delta_t, c_w, loc=loc_w, scale=scale_w))
    k_w = 2
    rows.append({
        "Model": "Weibull",
        "k": k_w,
        "LogLik": ll_w,
        "AIC": 2*k_w - 2*ll_w,
        "BIC": k_w*np.log(n) - 2*ll_w,
        "Interpretation": "Time-varying hazard (non-Markov)"
    })

    # --- Log-Normal (k=2 params) ---
    s_ln, loc_ln, scale_ln = stats.lognorm.fit(delta_t, floc=0)
    ll_ln = np.sum(stats.lognorm.logpdf(delta_t, s_ln, loc=loc_ln, scale=scale_ln))
    k_ln = 2
    rows.append({
        "Model": "Log-Normal",
        "k": k_ln,
        "LogLik": ll_ln,
        "AIC": 2*k_ln - 2*ll_ln,
        "BIC": k_ln*np.log(n) - 2*ll_ln,
        "Interpretation": "Peak response (narrative-specific)"
    })

    result = pd.DataFrame(rows).sort_values("AIC")
    result["ΔAIC"] = result["AIC"] - result["AIC"].min()
    return result


def ks_test_vs_shuffle(delta_t: np.ndarray):
    shuffled = rng.permutation(delta_t)
    D, p = stats.ks_2samp(delta_t, shuffled)
    return D, p


def plot_hazard(delta_t: np.ndarray, out_path: str = "figure3_hazard.png"):
    """
    Plot histogram + exponential fit + hazard function inset.
    Matches Figure 3 spec in Figure2.0.1.md
    """
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor("white")

    # — Left: histogram + exponential fit —
    ax = axes[0]
    ax.set_facecolor("white")
    counts, bins, _ = ax.hist(
        delta_t / 3600,                  # convert to hours
        bins=40, density=True,
        color="#4878CF", alpha=0.65, label="Empirical"
    )
    lam_hat = 1.0 / np.mean(delta_t)
    x = np.linspace(0, np.percentile(delta_t, 99) / 3600, 300)
    ax.plot(x, lam_hat * 3600 * np.exp(-lam_hat * x * 3600),
            "r--", linewidth=1.8,
            label=fr"Exp. fit ($\hat{{\lambda}}={lam_hat*3600:.4f}$/hr)")
    ax.set_xlabel(r"$\Delta t$ (hours)", fontsize=11)
    ax.set_ylabel("Density", fontsize=11)
    ax.set_title("Narrative Response Distribution", fontsize=12)
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)

    # — Right: hazard function λ(t) —
    ax2 = axes[1]
    ax2.set_facecolor("white")
    bin_centers = (bins[:-1] + bins[1:]) / 2
    pdf_est = counts
    cdf_est = np.cumsum(pdf_est) * np.diff(bins / 3600)[0] if len(bins) > 1 else np.cumsum(pdf_est)
    survival = np.maximum(1 - cdf_est, 1e-9)
    hazard = np.maximum(pdf_est / survival, 0)

    ax2.plot(bin_centers, hazard, color="#E84040", linewidth=1.8, label=r"$\hat{\lambda}(t)$")
    ax2.axhline(lam_hat * 3600, color="gray", linestyle="--",
                linewidth=1.2, label="Const. (Poisson)")
    ax2.set_xlabel(r"$\Delta t$ (hours)", fontsize=11)
    ax2.set_ylabel(r"$\hat{\lambda}(t)$", fontsize=11)
    ax2.set_title("Hazard Function", fontsize=12)
    ax2.legend(fontsize=9)
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[figure3] saved → {out_path}")


# ─────────────────────────────────────────────
# 3. VERIFICATION 1 — T(H) ABLATION
# ─────────────────────────────────────────────

def boltzmann_probs(scores: np.ndarray, T: float) -> np.ndarray:
    """Compute Boltzmann selection probabilities for given temperature T."""
    normed = (scores - scores.min()) / (scores.ptp() + 1e-9)
    logits = -normed / T
    logits -= logits.max()          # numerical stability
    probs = np.exp(logits)
    return probs / probs.sum()


def simulate_convergence(H: float, mode: str, n_trials: int = 100,
                         max_steps: int = 50) -> dict:
    """
    Simulate Boltzmann selection until convergence for a given H and temperature mode.
    Returns mean steps-to-convergence and final energy stability (std of last 10 J values).
    """
    steps_list, final_J_list = [], []
    for _ in range(n_trials):
        local_rng = np.random.default_rng(rng.integers(1e9))
        J_history = []
        J = local_rng.uniform(0.5, 1.0)
        for step in range(max_steps):
            candidates = J + local_rng.normal(0, 0.1 * (1 - step / max_steps), size=5)
            if mode == "dynamic":
                T = 0.1 + 0.9 * H
            elif mode == "const_high":
                T = 1.0
            else:                        # const_low
                T = 0.1
            probs = boltzmann_probs(candidates, T)
            J = local_rng.choice(candidates, p=probs)
            J_history.append(J)
            if step >= 10 and np.std(J_history[-5:]) < 0.01:
                break
        steps_list.append(step + 1)
        final_J_list.append(np.std(J_history[-10:]) if len(J_history) >= 10
                            else np.std(J_history))
    return {
        "mode": mode,
        "mean_steps": np.mean(steps_list),
        "std_steps":  np.std(steps_list),
        "energy_stability": np.mean(final_J_list)
    }


def run_ablation(df: pd.DataFrame) -> pd.DataFrame:
    H_values = df["entropy"].dropna().values
    # Sample 20 representative H values
    H_sample = rng.choice(H_values, size=min(20, len(H_values)), replace=False)
    rows = []
    for H in H_sample:
        for mode in ["dynamic", "const_high", "const_low"]:
            result = simulate_convergence(H, mode, n_trials=100)
            result["H"] = H
            rows.append(result)
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 4. VERIFICATION 2 — SIV TRANSITION MATRIX
# ─────────────────────────────────────────────
SIV_DIMS = ["siv_security","siv_economy","siv_tech",
            "siv_resource","siv_ideology","siv_environment"]


def build_transition_matrix(df: pd.DataFrame,
                             src: str = "jp",
                             tgt: str = "us") -> np.ndarray:
    """
    Learn a 6×6 SIV transition matrix M such that v_tgt ≈ M @ v_src.
    Uses least-squares regression per dimension.
    """
    from numpy.linalg import lstsq
    src_df = df[df["country_code"] == src].set_index("event_id")[SIV_DIMS]
    tgt_df = df[df["country_code"] == tgt].set_index("event_id")[SIV_DIMS]
    common = src_df.index.intersection(tgt_df.index)
    if len(common) < 10:
        print(f"[warn] Only {len(common)} common events for {src}→{tgt}")
        return np.eye(6)
    X = src_df.loc[common].values      # (n, 6)
    Y = tgt_df.loc[common].values      # (n, 6)
    M, _, _, _ = lstsq(X, Y, rcond=None)
    return M.T                         # (6, 6)


def evaluate_predictions(df: pd.DataFrame,
                          M: np.ndarray,
                          src: str = "jp",
                          tgt: str = "us",
                          test_frac: float = 0.2) -> dict:
    src_df = df[df["country_code"] == src].set_index("event_id")[SIV_DIMS]
    tgt_df = df[df["country_code"] == tgt].set_index("event_id")[SIV_DIMS]
    common = src_df.index.intersection(tgt_df.index)

    # Time-split
    split = int(len(common) * (1 - test_frac))
    test_ids = common[split:]
    if len(test_ids) == 0:
        return {}

    X_test = src_df.loc[test_ids].values
    Y_true = tgt_df.loc[test_ids].values

    def cosine_sim(A, B):
        dot = np.einsum("ij,ij->i", A, B)
        na  = np.linalg.norm(A, axis=1)
        nb  = np.linalg.norm(B, axis=1)
        denom = na * nb
        denom = np.where(denom < 1e-9, 1e-9, denom)
        return dot / denom

    # Baseline A: copy src SIV as-is
    cos_baseline_a = cosine_sim(X_test, Y_true).mean()

    # Baseline B: predict global mean of tgt
    global_mean = tgt_df.values.mean(axis=0, keepdims=True)
    Y_mean = np.repeat(global_mean, len(test_ids), axis=0)
    cos_baseline_b = cosine_sim(Y_mean, Y_true).mean()

    # GemminAI 2.0.1: apply transition matrix
    Y_pred = (M @ X_test.T).T
    cos_model = cosine_sim(Y_pred, Y_true).mean()

    return {
        "baseline_a_cosine":  round(float(cos_baseline_a), 4),
        "baseline_b_cosine":  round(float(cos_baseline_b), 4),
        "gemminai_cosine":    round(float(cos_model), 4),
        "relative_gain_pct":  round(
            (cos_model - cos_baseline_a) / (abs(cos_baseline_a) + 1e-9) * 100, 2),
        "n_test": len(test_ids)
    }


# ─────────────────────────────────────────────
# 5. FIGURE 4 — ENTROPY COMPARISON
# ─────────────────────────────────────────────

def compute_pair_entropy(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Pair entropy: variance of aggregated SIV vectors for same-event pairs.
    Noise entropy: variance for randomly shuffled pairs.
    """
    pair_entropies, noise_entropies = [], []
    events = [g for _, g in df.groupby("event_id") if len(g) >= 2]

    for grp in events:
        vecs = grp[SIV_DIMS].values
        agg = vecs.mean(axis=0)
        pair_entropies.append(float(np.var(agg)))

    # Noise: random pairs drawn from different events
    all_vecs = df[SIV_DIMS].values
    for _ in range(len(pair_entropies)):
        idx = rng.choice(len(all_vecs), size=2, replace=False)
        agg = all_vecs[idx].mean(axis=0)
        noise_entropies.append(float(np.var(agg)))

    return np.array(pair_entropies), np.array(noise_entropies)


def permutation_test(pair_ent, noise_ent, n_iter=PERM_ITERS) -> float:
    obs_diff = np.mean(noise_ent) - np.mean(pair_ent)
    combined = np.concatenate([pair_ent, noise_ent])
    n = len(pair_ent)
    count = 0
    for _ in range(n_iter):
        perm = rng.permutation(combined)
        diff = np.mean(perm[n:]) - np.mean(perm[:n])
        if diff >= obs_diff:
            count += 1
    return count / n_iter


def plot_entropy_comparison(pair_ent, noise_ent, p_val,
                            out_path="figure4_entropy.png"):
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    data   = [pair_ent, noise_ent]
    labels = ["Pair\n(T25-matched)", "Noise\n(random)"]
    bp = ax.boxplot(data, patch_artist=True, widths=0.45,
                    medianprops=dict(color="black", linewidth=1.5))
    colors = ["#4878CF", "#AAAAAA"]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("Entropy (SIV variance)", fontsize=11)
    ax.set_title("Figure 4: Entropy — Pair vs Noise", fontsize=12)

    p_str = "p < 0.001" if p_val < 0.001 else f"p = {p_val:.3f}"
    ax.text(1.5, max(np.percentile(noise_ent, 90),
                     np.percentile(pair_ent, 90)) * 1.05,
            p_str, ha="center", fontsize=10, color="#E84040")
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[figure4] saved → {out_path}")


# ─────────────────────────────────────────────
# 6. MAIN
# ─────────────────────────────────────────────

def main(data_path: str):
    print("=" * 55)
    print("benchmark_v2.py — Narrative Quantification 2.0.1")
    print("=" * 55)

    df = load_data(data_path)
    results = {}

    # ── Verification 3: Hazard & AIC/BIC ──────────────
    print("\n[V3] Extracting Δt pairs...")
    delta_t = extract_delta_t(df)
    print(f"     {len(delta_t):,} pairs found")

    model_tbl = fit_models(delta_t)
    print("\n[V3] Model comparison (AIC/BIC):")
    print(model_tbl.to_string(index=False))
    model_tbl.to_csv("model_comparison.csv", index=False)

    D, p_ks = ks_test_vs_shuffle(delta_t)
    print(f"\n[V3] KS test vs. shuffle: D={D:.4f}, p={p_ks:.2e}")
    results["ks_D"] = D
    results["ks_p"] = p_ks

    plot_hazard(delta_t)

    # ── Verification 1: T(H) Ablation ─────────────────
    print("\n[V1] Running T(H) ablation study...")
    ablation_df = run_ablation(df)
    summary = ablation_df.groupby("mode")[["mean_steps","energy_stability"]].mean()
    print(summary.round(4))
    ablation_df.to_csv("ablation_results.csv", index=False)

    # ── Verification 2: SIV Transition Matrix ─────────
    print("\n[V2] Building SIV transition matrix (JP→US)...")
    M = build_transition_matrix(df, src="jp", tgt="us")
    pred_metrics = evaluate_predictions(df, M, src="jp", tgt="us")
    if pred_metrics:
        print(f"     Baseline A (copy):  {pred_metrics['baseline_a_cosine']:.4f}")
        print(f"     Baseline B (mean):  {pred_metrics['baseline_b_cosine']:.4f}")
        print(f"     GemminAI 2.0.1:     {pred_metrics['gemminai_cosine']:.4f}")
        print(f"     Relative gain:      {pred_metrics['relative_gain_pct']:.1f}%")
    results.update(pred_metrics)

    # ── Figure 4: Entropy Comparison ──────────────────
    print("\n[F4] Computing entropy comparison...")
    pair_ent, noise_ent = compute_pair_entropy(df)
    p_perm = permutation_test(pair_ent, noise_ent)
    print(f"     Pair mean:  {pair_ent.mean():.6f}")
    print(f"     Noise mean: {noise_ent.mean():.6f}")
    print(f"     Permutation test p = {p_perm:.4f}")
    results["entropy_pair_mean"]  = pair_ent.mean()
    results["entropy_noise_mean"] = noise_ent.mean()
    results["permutation_p"]      = p_perm
    plot_entropy_comparison(pair_ent, noise_ent, p_perm)

    # ── Save consolidated CSV ──────────────────────────
    pd.DataFrame([results]).to_csv("evidence_v2_0_1.csv", index=False)
    print("\n[done] evidence_v2_0_1.csv written.")
    print("=" * 55)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="./data/narrative_articles.tsv",
                        help="Path to exported TSV from Hostinger")
    args = parser.parse_args()
    main(args.data)


# ─────────────────────────────────────────────
# APPENDIX: DATA EXPORT COMMAND (run in terminal)
# ─────────────────────────────────────────────
# 
# Step 1: Create export dir on Hostinger
#   ssh -p 65002 u991697696@145.79.26.56 "mkdir -p /tmp/export && chmod 777 /tmp/export"
#
# Step 2: Export (password via env var — do NOT paste inline)
#   export MYSQL_PWD=<your_password>
#   ssh -p 65002 u991697696@145.79.26.56 \
#     "mysql -u u991697696_aMM8W -S /tmp/mysql.sock u991697696_nW1eS \
#      -e \"SELECT fact_id, event_id, country_code, created_at, state_hash, \
#      strategic_interest_vector, audit_aura, \
#      JSON_UNQUOTE(JSON_EXTRACT(aiie_tags, '$.informational_entropy')) as entropy \
#      FROM narrative_articles ORDER BY created_at ASC\" \
#      --batch > /tmp/export/narrative_articles.tsv"
#
# Step 3: Download
#   mkdir -p ./data
#   scp -P 65002 u991697696@145.79.26.56:/tmp/export/narrative_articles.tsv ./data/
#
# Step 4: Clear password from env
#   unset MYSQL_PWD
#   history -c
#
# Step 5: Run benchmark
#   pip install pandas numpy scipy matplotlib
#   python benchmark_v2.py --data ./data/narrative_articles.tsv
