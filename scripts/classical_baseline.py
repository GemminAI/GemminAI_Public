"""
classical_baseline.py
GemminAI - Classical Baseline Simulator + Permutation Test
"""
import argparse
import numpy as np
import pandas as pd

def compute_siv_variance(s1, s2):
    return np.var(s1 - s2)

def compute_entropy(vec):
    vec = np.abs(vec)
    if vec.sum() == 0:
        return 0.0
    p = vec / vec.sum()
    return -np.sum(p * np.log(p + 1e-12))

def generate_classical_pair(n_dim=6):
    s1 = np.random.uniform(-1, 1, n_dim)
    s2 = np.random.uniform(-1, 1, n_dim)
    return s1, s2

def simulate_classical(n_samples):
    results = []
    for _ in range(n_samples):
        s1, s2 = generate_classical_pair()
        results.append({
            "variance": compute_siv_variance(s1, s2),
            "entropy":  compute_entropy(s1 - s2)
        })
    return pd.DataFrame(results)

def load_pairs(path, pair_type):
    df = pd.read_csv(path)
    df = df[df["type"] == pair_type]
    results = []
    for _, row in df.iterrows():
        s1 = row[[f"s1_{i}" for i in range(6)]].values.astype(float)
        s2 = row[[f"s2_{i}" for i in range(6)]].values.astype(float)
        results.append({
            "variance": compute_siv_variance(s1, s2),
            "entropy":  compute_entropy(s1 - s2)
        })
    return pd.DataFrame(results)

def permutation_test(observed, classical, n_perm=10000, metric="variance"):
    obs_mean = observed[metric].mean()
    cls_mean = classical[metric].mean()
    delta_obs = obs_mean - cls_mean

    combined = np.concatenate([observed[metric].values, classical[metric].values])
    n_obs = len(observed)
    count = 0
    for _ in range(n_perm):
        np.random.shuffle(combined)
        delta_perm = combined[:n_obs].mean() - combined[n_obs:].mean()
        if delta_perm >= delta_obs:
            count += 1
    p_value = count / n_perm
    return delta_obs, p_value

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", required=True)
    parser.add_argument("--n", type=int, default=5000)
    parser.add_argument("--perm", type=int, default=10000)
    args = parser.parse_args()

    print("Loading structured pairs (real observed)...")
    structured = load_pairs(args.pairs, "structured")
    print("Loading classical pairs (cross-category IID)...")
    classical_real = load_pairs(args.pairs, "classical")
    print("Simulating IID baseline (uniform random)...")
    classical_iid = simulate_classical(args.n)

    print("\n=== RESULT: Structured vs Cross-Category ===")
    print("structured mean_var:  {:.6f}".format(structured["variance"].mean()))
    print("classical  mean_var:  {:.6f}".format(classical_real["variance"].mean()))
    print("structured mean_ent:  {:.6f}".format(structured["entropy"].mean()))
    print("classical  mean_ent:  {:.6f}".format(classical_real["entropy"].mean()))

    print("\n--- Permutation Test (variance) ---")
    dv, pv = permutation_test(structured, classical_real, args.perm, "variance")
    print("delta_var:  {:.6f}".format(dv))
    print("p-value:    {:.6f}  ({})".format(pv, "SIGNIFICANT" if pv < 0.05 else "not significant"))

    print("\n--- Permutation Test (entropy) ---")
    de, pe = permutation_test(structured, classical_real, args.perm, "entropy")
    print("delta_ent:  {:.6f}".format(de))
    print("p-value:    {:.6f}  ({})".format(pe, "SIGNIFICANT" if pe < 0.05 else "not significant"))

    print("\n=== RESULT: Structured vs IID Uniform ===")
    print("structured mean_var:  {:.6f}".format(structured["variance"].mean()))
    print("iid        mean_var:  {:.6f}".format(classical_iid["variance"].mean()))

    print("\n--- Permutation Test vs IID (variance) ---")
    dv2, pv2 = permutation_test(structured, classical_iid, args.perm, "variance")
    print("delta_var:  {:.6f}".format(dv2))
    print("p-value:    {:.6f}  ({})".format(pv2, "SIGNIFICANT" if pv2 < 0.05 else "not significant"))

    # Save
    structured["type"] = "structured"
    classical_real["type"] = "classical_cross"
    classical_iid["type"] = "classical_iid"
    out = pd.concat([structured, classical_real, classical_iid])
    out.to_csv("/home/tomona/results_classical.csv", index=False)
    print("\nSaved: results_classical.csv")

if __name__ == "__main__":
    main()
