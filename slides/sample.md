---
marp: true
theme: catech
paginate: true
math: katex
header: name
footer: "線形回帰入門"
---

<!-- _class: title -->

# 線形回帰入門

色付けサンプルスライド

---

# 線形回帰とは

<span class="blue-lined">教師あり学習</span>の最も基本的なアルゴリズム

入力 $x$ から出力 $y$ を予測する<span class="dotted">線形なモデル</span>を学習する

$$
\hat{y} = w_0 + w_1 x_1 + w_2 x_2 + \cdots + w_n x_n
$$

- $w_0$: <span class="blue">バイアス項</span>
- $w_1, \ldots, w_n$: <span class="blue">重みパラメータ</span>

---

# 損失関数

パラメータの最適化には<span class="orange-lined">平均二乗誤差 (MSE)</span>を用いる

$$
\mathcal{L}(w) = \frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2
$$

- $\mathcal{L}$ が<span class="red">大きい</span> → 予測が悪い
- $\mathcal{L}$ が<span class="green">小さい</span> → 予測が良い

目標: $\mathcal{L}(w)$ を<span class="dotted">最小化</span>する $w$ を見つける

---

# 最適化手法

**正規方程式** <span class="gray">（解析解が存在する場合）</span>

$$
w = (X^\top X)^{-1} X^\top y
$$

**勾配降下法**（大規模データ向け）{.gray}



$$
w \leftarrow w - \eta \nabla_w \mathcal{L}(w)
$$

- $\eta$: <span class="orange-lined">学習率</span> — 大きすぎると<span class="red">発散</span>、小さすぎると<span class="red">収束が遅い</span>

---

# 過学習と正則化

モデルが訓練データに<span class="red">過剰適合</span>すると汎化性能が低下する

対策: 損失関数に<span class="blue-lined">正則化項</span>を追加

| 手法 | 正則化項 | 特徴 |
| ---- | -------- | ---- |
| Ridge (L2) | $\lambda \|w\|_2^2$ | <span class="green">全体を縮小</span> |
| Lasso (L1) | $\lambda \|w\|_1$ | <span class="green">スパース解</span>（特徴選択） |

<span class="dotted">λ が大きいほど正則化が強くなる</span>

---

# まとめ

- 線形回帰は<span class="blue-lined">最も基本的な回帰モデル</span>
- 損失関数の<span class="orange-lined">最小化</span>によりパラメータを学習
- <span class="red">過学習</span>には正則化で対処
- 実用上は<span class="dotted">特徴量エンジニアリング</span>が重要
