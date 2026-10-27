# Meeting Slides

[Marp](https://marp.app/) を使ったプレゼンテーションスライド
<img width="1243" height="700" alt="Image" src="https://github.com/user-attachments/assets/3f0d9ac0-ce74-41b7-850a-09415b05c729" />
abap34さんの https://github.com/abap34/slide-template を元に作成しました

## ディレクトリ構成

```
slides/             … Markdown ソース（スライド本体）
html/               … HTML 出力（gitignore）
pdf/                … PDF 出力（gitignore）
pptx/               … PPTX 出力（gitignore）
style.css           … カスタムテーマ（kyomu）
science-tokyo.css   … Science Tokyo テーマ（既存素材・配色を基に部品を再設計）
catalog/            … 65型の対応表と固定revisionの参照索引
docs/               … 作例索引・図の更新手順
assets/science-tokyo/ … ロゴ・背景素材（テーマに同梱・差し替え用）
engine.mjs          … Markdown 拡張エンジン
```

テーマは `--theme-set` で両方登録済み。各スライドの front-matter の `theme:` で切り替える
（`theme: kyomu` または `theme: science-tokyo`）。

## セットアップ

```bash
npm install
```

## 使い方

### プレビュー（Watchモード）

`slides/` 内の全ファイルを監視し、保存時に `html/` へ自動再生成する。

```bash
npm run dev
```

### エクスポート

```bash
# HTML（slides/ → html/）
npm run build

# PDF（slides/ → pdf/）
npm run build:pdf

# PPTX（slides/ → pptx/）
npm run build:pptx
```

## Science Tokyo テーマ

東京科学大学（Institute of Science Tokyo）の既存素材・配色を基にした、16:9の非公式Marpテーマです。
ブランドカラー `#1C3077` / サブカラー `#7F96C2` と、従来のフォント設定を維持しています。
カードは角丸・影を使わず、面・罫線・見出し帯で整理します。

雛形は **`slides/science-tokyo-template.md`**。コピーして中身を書き換えれば使えます。
65型の構成を探す場合は **`slides/science-tokyo-catalog.md`** と
[作例索引・使い方](docs/science-tokyo-catalog.md) を使ってください。
作例の構成・数値は説明用の架空例で、実際の研究結果ではありません。

### 65型の見本帳と図の編集

- コピー元：`slides/science-tokyo-catalog.md`。先頭のfront-matterと、使いたいスライドをコピーします。
- 対応表：`catalog/science-tokyo.json`。参照側の型IDと、作例のページ・実装方法を対応付けています。
- 基本部品：Markdownのコンテナを使用。既存の `::: card`・`::: cols` なども引き続き使用できます。
- 複雑な図：`assets/science-tokyo/diagrams/science-tokyo-diagrams.pptx` が編集用原本です。図の画像を書き出してMarpに配置します。
- 図の更新：[PPTX原本と画像の更新手順](docs/science-tokyo-diagrams.md)。PNGだけを編集せず、原本も保持してください。

PPTX原本を**手動編集した後**は `npm run diagrams:export` で画像だけを更新します。
`npm run diagrams:build` は原本も生成し直すため、手動編集を上書きします。

図を再生成・再書き出しする環境には、Pythonの専用仮想環境、LibreOffice、popplerが必要です。
既に同梱された図を使うだけなら、通常の `npm install` とMarpで利用できます。

```bash
python3 -m venv .venv-diagrams
.venv-diagrams/bin/python -m pip install -r requirements-diagrams.txt
npm run diagrams:export
```

### 完成確認

```bash
npm test                 # 部品・構成・既存記法の回帰テスト
npm run test:artifacts   # 出力検証ツールのテスト
npm run test:diagrams    # 編集用PPTX・画像のテスト
npm run verify          # テスト → 3形式のビルド → 全65型の表示検証
```

`npm run verify` はローカルのChrome、LibreOffice、popplerと上記Python環境を使用します。
Chromeの場所が異なる環境では `CHROME_PATH=/path/to/chrome` を指定します。
HTML・PDF・Marp出力PPTXを実際に描画し、ページ数・画像欠落・はみ出し・重なり・
角丸や影の混入・形式間の画像差分を検査します。
結果は `.verification/layout-report.json`・`.verification/artifact-report.json`、
全ページの画像と3形式の比較シートは `.verification/` 以下です。
形式間比較は、成功したHTML検査記録とHTML・対応表・各PNGのSHA-256が一致する場合だけ実行します。
単独で `npm run verify:artifacts` を使う場合も、先に `npm run verify:layout` で記録を更新してください。
機械検査は内容の正しさやすべての視認性を保証しないため、比較シートも目視してください。

**編集用の図PPTXと、Marpから書き出す資料全体のPPTXは別物です。**
通常の `npm run build:pptx` の出力について、内部の文字・図形を個別編集できるとは保証しません。
ロゴ・配色を含むScience Tokyo素材の利用は所属組織の規程を確認してください。
本テーマは大学や参照リポジトリの作成者による公式・推奨版を表すものではありません。

### 使い方

front-matter で `theme: science-tokyo` を指定する。

```markdown
---
marp: true
theme: science-tokyo
paginate: true
---

<!-- _class: title -->
# プレゼンタイトル
## 氏名 / Your Name
###### 役職・所属
イベント名・日付

---

<!-- _class: section -->
# 1. 章タイトル

---

# コンテンツのタイトル
## 見出し（h2）
本文…（==ハイライト== や **強調**）
```

### クラス・記法

| 指定 | 用途 |
|--|--|
| `<!-- _class: title -->` | 表紙（ネイビー背景・白文字・ロゴ右下） |
| `<!-- _class: section -->` | 中表紙／章扉（ネイビー） |
| `<!-- _class: section-light -->` | 中表紙／章扉（ライト） |
| （無印） | 本文ページ（右上ロゴ＋タイトル下線＋右端バー＋ページ番号） |
| `#` / `##` / `###` | タイトル / 見出し / 小見出し |

レイアウト・装飾ユーティリティ:
`::: cols` `::: cols-3`（カラム）、`::: box` `::: card`（枠カード）、
`::: navy-card`（ネイビー見出しカード）、`::: callout`（左ライン強調）、`::: lead`（リード文）、
`.cite`（出典）、文字色 `**text**{.navy}` `**text**{.blue}` `**text**{.red}` `**text**{.green}` `**text**{.gold}` `**text**{.gray}`、
画像 `![center] ![wide] ![medium] ![short]`。

### ロゴ・背景の差し替え

素材は `assets/science-tokyo/`（`logo.png` / `cover.png` / `section.png` ほか）。
テーマには base64 で埋め込み済みのため、差し替える場合は画像を置き換えたうえで
`science-tokyo.css` 末尾の `ASSET DATA` ブロックを再生成する。

## Markdown 拡張構文

`engine.mjs` により、以下の拡張構文が使える（Marp CLI経由のみ。VSCodeプレビューでは反映されない）。

### マーク（markdown-it-mark）

```markdown
==ハイライトされるテキスト==
```

### 属性付与（markdown-it-attrs）

要素に class / id / style を直接付与できる。
`<span class="blue">...</span>` の代わりに、強調や画像などへ直接 class を付けられる。

```markdown
**太字**{.blue}
# 見出し {.special}
**テキスト**{style="color:red"}
出典：サンプルデータ{.cite}
```

### コンテナ（markdown-it-container）

`box`, `card`, `navy-card`, `callout`, `lead`, `center`, `small`, `xs`, `note`, `warning`, `info`
などが使える。`<div class="box">...</div>` の代わりに書ける。

```markdown
::: box
枠付きカード
:::

::: callout
重要な補足
:::

::: note
補足テキスト
:::
```

### カラム

`::: cols` は 2 カラム、`::: cols-3` は 3 カラム。カラムの区切りは `|||`。

```markdown
::: cols

### 左カラム

- ポイント 1
- ポイント 2

|||

### 右カラム

::: callout
重要な点を強調
:::

:::
```

3 カラムのカードも HTML なしで書ける。

```markdown
::: cols-3

::: navy-card
#### タイトル A
本文
:::

|||

::: navy-card
#### タイトル B
本文
:::

|||

::: navy-card
#### タイトル C
本文
:::

:::
```
