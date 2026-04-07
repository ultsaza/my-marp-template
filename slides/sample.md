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

**教師あり学習**{.blue-lined}の最も基本的なアルゴリズム

入力 $x$ から出力 $y$ を予測する**線形なモデル**{.dotted}を学習する

$$
\hat{y} = w_0 + w_1 x_1 + w_2 x_2 + \cdots + w_n x_n
$$

- $w_0$: **バイアス項**{.blue}
- $w_1, \ldots, w_n$: **重みパラメータ**{.blue}

---

# 損失関数

パラメータの最適化には**平均二乗誤差 (MSE)**{.orange-lined}を用いる

$$
\mathcal{L}(w) = \frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2
$$

- $\mathcal{L}$ が**大きい**{.red} → 予測が悪い
- $\mathcal{L}$ が**小さい**{.green} → 予測が良い

目標: $\mathcal{L}(w)$ を**最小化**{.dotted}する $w$ を見つける

---

# 最適化手法

**正規方程式** **（解析解が存在する場合）**{.gray}

$$
w = (X^\top X)^{-1} X^\top y
$$

**勾配降下法**（大規模データ向け）{.gray}



$$
w \leftarrow w - \eta \nabla_w \mathcal{L}(w)
$$

- $\eta$: **学習率**{.orange-lined} — 大きすぎると**発散**{.red}、小さすぎると**収束が遅い**{.red}

---

# 過学習と正則化

モデルが訓練データに**過剰適合**{.red}すると汎化性能が低下する

対策: 損失関数に**正則化項**{.blue-lined}を追加

| 手法 | 正則化項 | 特徴 |
| ---- | -------- | ---- |
| Ridge (L2) | $\lambda \|w\|_2^2$ | **全体を縮小**{.green} |
| Lasso (L1) | $\lambda \|w\|_1$ | **スパース解**{.green}（特徴選択） |

**λ が大きいほど正則化が強くなる**{.dotted}

---

# まとめ

- 線形回帰は**最も基本的な回帰モデル**{.blue-lined}
- 損失関数の**最小化**{.orange-lined}によりパラメータを学習
- **過学習**{.red}には正則化で対処
- 実用上は**特徴量エンジニアリング**{.dotted}が重要
