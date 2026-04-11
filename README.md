# GemminAI — Public Repository

**Gemmina Intelligence LLC**  
[gemminai.com](https://gemminai.com) · [acta-aiie.org](https://acta-aiie.org) · [@jpGemminai](https://x.com/jpGemminai)

---

## What is GemminAI?

GemminAI is a geopolitical intelligence platform that applies **Narrative Physics** — a mathematically formalized framework for measuring how stories propagate, stabilize, and diverge across regions and time.

Every narrative state is assigned a deterministic identifier (**T25 state_hash**) via JSON Canonicalization Scheme (RFC 8785) + SHA-256, making all analytical outputs independently verifiable.

---

## This Repository

This repository contains the **publicly verifiable layer** of the GemminAI system:

```
scripts/
  benchmark_v2.py       — Evidence generation script (NQ 2.0.1)
  measurement_plan.md   — Computational measurement specification
RELEASE_NOTES.md        — System update history
```

### scripts/benchmark_v2.py

A self-contained benchmarking script that reproduces the empirical claims in the companion paper *Narrative Quantification 2.0.1*:

- **V1**: Ablation study of the temperature function T(H) = 0.1 + 0.9H
- **V2**: SIV transition matrix predictive accuracy (JP→US narrative propagation)
- **V3**: Hazard function λ(t) estimation + AIC/BIC model comparison (Exponential / Weibull / Log-Normal)
- **F4**: Entropy comparison between structurally paired and random narrative states

---

## Companion Paper

**Narrative Quantification 2.0: A Framework for the Observability of Reasoning Dynamics in Structured State Spaces**

→ [acta-aiie.org](https://acta-aiie.org)

---

## Protocol Specification

The **Acta AIIE Protocol** — the constitutional document governing all GemminAI state representations — is maintained at:

→ [github.com/GemminAI/Acta-AIIE](https://github.com/GemminAI/Acta-AIIE)

---

## Data

The full dataset (9,378 narrative instances / 1,563 events) is not publicly distributed.  
A sample (`data/sample_100.tsv`) is provided for reproducibility verification.

---

*Gemmina Intelligence LLC. — Crystallizing the noise of the world.*
