# 計測実装予定書
## Narrative Quantification 2.0.1 — Evidence Generation Plan

**作成日**: 2026-04-11  
**対象スクリプト**: `benchmark_v2.py`  
**組織**: Gemmina Intelligence LLC

---

## 1. 目的と論文上の位置づけ

本スクリプトは、査読指摘への対応として以下3検証の証拠データを自動生成する。
生成された数値・グラフは論文の該当セクションへ直接流し込む。

| 検証 | 論文セクション | 生成物 |
|---|---|---|
| V1: T(H) アブレーション | §Appendix C + §1b対応 | `ablation_results.csv` |
| V2: SIV 遷移行列 | §9.3 predictive accuracy | `evidence_v2_0_1.csv` |
| V3: ハザード関数 + AIC/BIC | §8.X.5 + Figure 3 inset | `model_comparison.csv` + `figure3_hazard.png` |
| F4: エントロピー比較 | §9.1 + Figure 4 | `figure4_entropy.png` |

---

## 2. データ依存関係

### 入力ファイル
```
./data/narrative_articles.tsv
```

Hostinger MySQL から以下クエリで取得：

```sql
SELECT fact_id, event_id, country_code, created_at, state_hash,
       strategic_interest_vector, audit_aura,
       JSON_UNQUOTE(JSON_EXTRACT(aiie_tags, '$.informational_entropy')) as entropy
FROM narrative_articles
ORDER BY created_at ASC
```

### 必須カラム

| カラム | 用途 | 検証 |
|---|---|---|
| `event_id` | ペアリング・Δt計算 | V2, V3, F4 |
| `country_code` | JP→US 遷移行列 | V2 |
| `created_at` | Δt（秒）算出 | V3 |
| `strategic_interest_vector` | SIV 6次元ベクトル JSON | V2, F4 |
| `aiie_tags.informational_entropy` | H値（Boltzmann温度） | V1 |

---

## 3. 検証別 実装詳細と後続作業との整合性

### V1: T(H) アブレーション（§1b 査読対応）

**実装方針**  
本番パイプラインには触れない。DBの`entropy`カラム分布から20点をサンプリングし、
`dynamic / const_high / const_low` の3モードを各100試行シミュレート。

**出力**  
```
ablation_results.csv
  columns: mode, H, mean_steps, std_steps, energy_stability
```

**論文への流し込み先**  
Appendix C に以下のテーブルとして挿入：

```
Table C.1: Convergence comparison across temperature modes
Mode          | Mean Steps | Energy Stability
dynamic T(H)  |    XX.X    |     X.XXXX
const T=1.0   |    XX.X    |     X.XXXX
const T=0.1   |    XX.X    |     X.XXXX
```

**後続作業との整合性**  
- POST-4 Event Intelligence Engine 実装時に `thermodynamic_phase` のフィードバックループと
  このアブレーション結果を突き合わせて実装パラメータを確定する。
- `narrative_dynamics_engine.py` の T定義修正（RFC-0003乖離問題）の根拠データとしても使用可能。

---

### V2: SIV 遷移行列（§9.3 predictive accuracy）

**実装方針**  
JP→US の 6×6 遷移行列 M を最小二乗回帰で学習（80/20 時系列分割）。

```
入力: SIV_jp（6次元）
予測: SIV_us ≈ M @ SIV_jp
評価: コサイン類似度
```

**ベースライン定義**

| モデル | 定義 |
|---|---|
| Baseline A | JP の SIV をそのままコピー（無変化モデル） |
| Baseline B | US の全体平均ベクトルを出力 |
| GemminAI 2.0.1 | 遷移行列 M を適用した予測 |

**出力**  
```
evidence_v2_0_1.csv
  columns: baseline_a_cosine, baseline_b_cosine, gemminai_cosine,
           relative_gain_pct, n_test, ks_D, ks_p,
           entropy_pair_mean, entropy_noise_mean, permutation_p
```

**論文への流し込み先**  
§9.3 末尾に以下を追記：

> The proposed model achieves a cosine similarity of X.XX, compared to
> X.XX for Baseline A (copy) and X.XX for Baseline B (global mean),
> representing a relative improvement of XX%.

**後続作業との整合性**  
- 遷移行列 M の構造は POST-4 の `EventRelationグラフ` 実装の設計根拠になる。
- Phase 1.5 学術連携フェーズでの JST 申請資料に数値を転用可能。

---

### V3: ハザード関数 + AIC/BIC（§8.X.5 + Figure 3）

**実装方針**  
同一 `event_id` を持つ異国ペアの `created_at` 差分 Δt（秒）を全組み合わせで抽出。
3モデルをフィッティングし AIC/BIC で比較。

**フィッティングモデル**

| モデル | パラメータ数 | 解釈 |
|---|---|---|
| 指数分布 | 1 | 記憶なし（Poisson過程） |
| Weibull分布 | 2 | 時変ハザード（非マルコフ） |
| 対数正規分布 | 2 | ピーク応答（ナラティブ特有） |

**期待される結果と論文上の意味**

- Weibull or 対数正規の AIC が指数分布より低い
  → 「ナラティブ場には非マルコフ的な記憶（Memory Kernel）がある」の最強証明
- 指数分布の AIC が最小だった場合
  → §8.X.5 の記述を「Poisson過程との整合性」として再解釈（棄却ではなく収束の証拠）

**出力**  
```
model_comparison.csv
  columns: Model, k, LogLik, AIC, BIC, ΔAIC, Interpretation

figure3_hazard.png
  左: ヒストグラム + 指数フィット（赤点線）
  右: ハザード関数 λ(t) の実測値 + Poisson定数との対比
```

**後続作業との整合性**  
- Figure 3 キャプションの `(see §8.X.5)` と双方向参照が完成する。
- AIC/BIC テーブルは Table 2 として §8.X.5 直後に配置予定。
- 対数正規フィットが勝った場合、POST-5 Intelligence Log の
  「ナラティブ応答予測機能」の理論根拠になる。

---

### F4: エントロピー比較（§9.1 + Figure 4）

**実装方針**  
同一 T25 を持つペアの SIV 分散（Pair）と、ランダムペアの SIV 分散（Noise）を比較。
Permutation test（1,000回）で有意差を検定。

**出力**  
```
figure4_entropy.png
  箱ひげ図 + p値オーバーレイ
```

**論文への流し込み先**  
Figure 4 キャプションの `p < 0.001` を実測値に差し替え。

---

## 4. 実行スケジュール（推奨）

```
土曜午前  Hostinger SSH でデータエクスポート（下記手順参照）
土曜午後  benchmark_v2.py 実行・CSV確認
日曜午前  figure3_hazard.png / figure4_entropy.png をグラフ確認・調整
日曜午後  論文 §8.X.5 / §9.3 / Appendix C に数値を流し込み
月〜火    Figure 3・4 の最終版を論文 PDF に組み込み
水〜木    1b/2b 修正完了 → 投稿前最終確認
```

---

## 5. セキュリティ上の注意（データエクスポート手順）

```bash
# Step 1: export dir 作成
ssh -p 65002 u991697696@145.79.26.56 \
  "mkdir -p /tmp/export && chmod 777 /tmp/export"

# Step 2: パスワードを環境変数経由で渡す（履歴に残さない）
export MYSQL_PWD=<your_password>
ssh -p 65002 u991697696@145.79.26.56 \
  "mysql -u u991697696_aMM8W -S /tmp/mysql.sock u991697696_nW1eS \
   -e \"SELECT fact_id, event_id, country_code, created_at, state_hash, \
   strategic_interest_vector, audit_aura, \
   JSON_UNQUOTE(JSON_EXTRACT(aiie_tags, '$.informational_entropy')) as entropy \
   FROM narrative_articles ORDER BY created_at ASC\" \
   --batch > /tmp/export/narrative_articles.tsv"

# Step 3: ローカルへダウンロード
mkdir -p ./data
scp -P 65002 u991697696@145.79.26.56:/tmp/export/narrative_articles.tsv ./data/

# Step 4: パスワードをクリア
unset MYSQL_PWD
history -c
```

---

## 6. 出力ファイル一覧

| ファイル | 用途 | 論文への流し込み先 |
|---|---|---|
| `evidence_v2_0_1.csv` | 全検証の統合数値 | §9.1 / §9.3 |
| `model_comparison.csv` | AIC/BIC 比較テーブル | §8.X.5 Table 2 |
| `ablation_results.csv` | T(H) アブレーション | Appendix C Table C.1 |
| `figure3_hazard.png` | ハザード関数グラフ | Figure 3 inset |
| `figure4_entropy.png` | エントロピー比較グラフ | Figure 4 |

---

*Gemmina Intelligence LLC. — Pure Information Laboratory*  
*「データが来てから論文に書く。推測で埋めない。」*
