# Meeting Slides

Marp を使ったプレゼンテーションスライド

## ディレクトリ構成

```
slides/       … Markdown ソース（スライド本体）
html/         … HTML 出力（gitignore）
pdf/          … PDF 出力（gitignore）
pptx/         … PPTX 出力（gitignore）
style.css     … カスタムテーマ
engine.mjs    … Markdown 拡張エンジン
```

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

## Markdown 拡張構文

`engine.mjs` により、以下の拡張構文が使える（Marp CLI経由のみ。VSCodeプレビューでは反映されない）。

### マーク（markdown-it-mark）

```markdown
==ハイライトされるテキスト==
```

### 属性付与（markdown-it-attrs）

要素に class / id / style を直接付与できる。

```markdown
**太字**{.blue}
# 見出し {.special}
テキスト{style="color:red"}
```

### コンテナ（markdown-it-container）

`note`, `warning`, `info` が使える。

```markdown
:::note
補足テキスト
:::
```
