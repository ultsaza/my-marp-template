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
science-tokyo.css   … Science Tokyo テーマ（公式PPTXを再現）
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

東京科学大学（Institute of Science Tokyo）公式 PowerPoint テンプレート（16:9）を
Marp 用に再現したテーマ。ブランドカラー `#1C3077` / サブカラー `#7F96C2` / 游ゴシック。

雛形は **`slides/science-tokyo-template.md`**。コピーして中身を書き換えれば使えます。

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
