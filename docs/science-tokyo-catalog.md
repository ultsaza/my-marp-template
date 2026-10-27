# Science Tokyo 65型カタログ

基本30型 `b01`〜`b30`、追加35型 `m01`〜`m35` の全65型を、各1枚で試せる Marp の作例集です。見た目の型だけを参照し、Science Tokyo の既存の配色・書体・ロゴを使います。学術発表・研究計画を想定した文章・数値・資料断片は**すべて説明用の架空例**であり、実在する機関の活動、研究結果、制度、実績を示しません。テーマの利用が機関の推薦・承認を意味するものではありません。

## ファイルと編集方法

- 作例の原稿：`slides/science-tokyo-catalog.md`。下表の「通番」は PDF・HTML・Marp出力の1始まりのスライド番号です。追加パーツの `m01` は通番31です。
- 機械可読の対応表：`catalog/science-tokyo.json`。`key` と `id` は参照元の識別子、`title` は参照元の型名、`slide` は通番、`source` は作例原稿、`diagram` は PNG のリポジトリ相対パスです。
- `markdown` 43型：本文・表・段階・柱・比較・Q&Aなどを Marp 上で編集します。カードに置き換えず、型が表す情報の関係を保ってください。
- `pptx-image` 22型：Marp は型名・図・短い識別キャプションだけを配置します。図の編集元は `assets/science-tokyo/diagrams/science-tokyo-diagrams.pptx` です。図中文字・図形・グラフの修正後は PNG を再出力します。生成手順は `docs/science-tokyo-diagrams.md` を参照してください。
- コピー：`<!-- pattern: b09 axis_table -->` のようなコメントを検索し、次のスライド区切り `---` の直前までをコピーします。先頭の YAML frontmatter は資料全体で一度だけ置き、表紙も1型として数えます。`#` が型名、`##` 以下が例の見出しです。本番では型名を主張文に置き換えます。
- 画像は `../assets/science-tokyo/diagrams/{id}.png` として参照するため、原稿を `slides/` 配下に置くとそのまま使えます。別の場所へコピーしたときは相対パスを更新してください。
- 作例の可視キャプションは `key / id`、非表示コメントは固定リビジョン・参照ファイル・パーツ番号を保持します。原典への参照と、作例の架空データを混同しないでください。

## 検証

```sh
node --test tests/catalog.test.mjs
```

インストール済み Marp で YAML frontmatter がスライドに数えられないこと、`##` が別スライドに数えられないこと、パターンコメントが `render().comments` にスライド順で保持されることを先に特性テストしています。全65型の順序・固有ID・通番・型名・図参照・フッター・43/22の分担と、下表の全65行を静的テストで確認します。PNG の実在、解像度、編集可能PPTX、実際の改ページ・はみ出しは、図生成および全体の出力・目視検証で別途確認します。静的テストはその代用ではありません。

## 参照元（固定版）

- リポジトリ：`https://github.com/carnot-tech/jinba-consulting-pptx-skill`
- リビジョン：`e5f35e57e14d3998249a559c620a9286c95b4595`
- 型ID・型名の正典：同リビジョンの `references/archetype-catalog.md`。
- 基本パーツ原稿：`templates/freeform_parts_16x9.html`（下表「基本」の番号）。
- 追加パーツ原稿：`templates/freeform_parts_more_16x9.html`（下表「追加」の番号）。

下表の原典リンクは上記リビジョンに固定しています。型IDはそのままコピーできます。型名の長い括弧内説明は図版スライドの見出しでは省略し、対応表には原文を保持します。

## 全65型の対応表

| キー | 通番 | 原典ID | 型名 | モード | 原典の所在 | 見せる関係・使いどころ |
|:--|--:|:--|:--|:--|:--|:--|
| b01 | 1 | `title_page` | 表紙 | `markdown` | [基本 01](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 題名・発表者・場を置く |
| b02 | 2 | `overview_map` | 全体マップ | `markdown` | [基本 02](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 目的・領域・共通基盤の関係 |
| b03 | 3 | `table_of_contents` | 目次 | `markdown` | [基本 03](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 議論の順序を予告する |
| b04 | 4 | `section_divider` | 章扉 | `markdown` | [基本 04](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 次の章へ視点を切り替える |
| b05 | 5 | `chevron_steps` | 矢羽（プロセス・変遷） | `markdown` | [基本 05](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 工程の進行を矢羽で示す |
| b06 | 6 | `premise_conclusion` | 前提→帰結の2カラム | `markdown` | [基本 06](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 前提から帰結を導く |
| b07 | 7 | `stat_table_readout` | 大型数値の表＋読み取り | `markdown` | [基本 07](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 数値の表から意味を読み取る |
| b08 | 8 | `card_grid_2x2` | 並列カード 2×2 | `markdown` | [基本 08](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 同格の四要素を並べる |
| b09 | 9 | `axis_table` | 軸のある表 | `markdown` | [基本 09](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 縦軸と横軸の交点を読む |
| b10 | 10 | `back_cover` | 裏表紙 | `markdown` | [基本 10](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 議論を閉じ、次の接点を残す |
| b11 | 11 | `claim_panel_figure` | 主張パネル＋図 | `markdown` | [基本 11](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 主張を関係図で補う |
| b12 | 12 | `lever_effect_table` | 打ち手の効果表 | `markdown` | [基本 12](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 打ち手と想定効果を結ぶ |
| b13 | 13 | `status_heatmap_comment` | 状態ヒートマップ＋右コメント | `markdown` | [基本 13](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 状態の分布から次の対応を示す |
| b14 | 14 | `harvey_ball_table` | 充足度評価表（ハーベイボール） | `markdown` | [基本 14](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 要件の充足度を円で比較する |
| b15 | 15 | `dot_matrix_share` | 割合のドットマトリクス | `pptx-image` | [基本 15](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 全体に占める割合を点で数える |
| b16 | 16 | `progress_bubble_matrix` | 進捗バブル行列 | `pptx-image` | [基本 16](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 工程と担当の進捗・規模を見る |
| b17 | 17 | `ranked_bar_annotated` | 分布の順位棒＋注記 | `pptx-image` | [基本 17](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 順位分布の注目点を示す |
| b18 | 18 | `scatter_annotated` | 注記つき散布図 | `pptx-image` | [基本 18](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 二変数の関係と例外を読む |
| b19 | 19 | `pillars_foundation` | 柱＋土台 | `markdown` | [基本 19](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 複数の柱を共通の土台で支える |
| b20 | 20 | `opposing_chevrons` | 対向シェブロン | `markdown` | [基本 20](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 両側の要請を接点で合わせる |
| b21 | 21 | `evidence_clip_grid` | 外部動向の根拠グリッド | `markdown` | [基本 21](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 資料断片と検討点を対応付ける |
| b22 | 22 | `proportional_circles` | 比例円の対比 | `pptx-image` | [基本 22](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 面積で規模を比べる |
| b23 | 23 | `delta_bars_totals` | 増減の縦棒＋左右合計 | `pptx-image` | [基本 23](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 増減と前後の合計をつなぐ |
| b24 | 24 | `scenario_lines_cagr` | シナリオ線＋成長率チップ | `pptx-image` | [基本 24](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 将来の経路と成長率を比較する |
| b25 | 25 | `research_basis` | 調査の土台 | `markdown` | [基本 25](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 調査の対象・方法・境界を決める |
| b26 | 26 | `issue_action_columns` | 課題と打ち手の2カラム | `markdown` | [基本 26](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 課題と打ち手を並べて対応させる |
| b27 | 27 | `agenda_separator` | セパレーター（章扉＝アジェンダ再掲） | `markdown` | [基本 27](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | アジェンダを再掲し現在地を示す |
| b28 | 28 | `swimlane_numbered_notes` | スイムレーン＋番号の付箋（縦＝担い手・横＝業務の流れに課題・適用例を番号で重ね、右に一覧） | `pptx-image` | [基本 28](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 担当と工程に課題番号を重ねる |
| b29 | 29 | `front_back_two_tier` | 表と裏の2段（上段＝利用者から見た流れ、下段＝裏側の処理を縦に対応。指示の前後の比較にも使う） | `pptx-image` | [基本 29](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 利用者の流れと裏側の処理を対応させる |
| b30 | 30 | `qa_list` | 一問一答（質問は相手の言葉のまま、回答と区切り線で分ける） | `markdown` | [基本 30](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_16x9.html) | 相手の質問に一つずつ答える |
| m01 | 31 | `executive_summary` | エグゼクティブサマリー | `markdown` | [追加 01](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 結論・論点・判断依頼を一覧にする |
| m02 | 32 | `evidence_basis` | 調査の土台 | `markdown` | [追加 02](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 検討に使う材料と限界を示す |
| m03 | 33 | `big_stat_pair` | 大型数値の対比 | `markdown` | [追加 03](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 二つの大きな数値を対比する |
| m04 | 34 | `kpi_dashboard` | KPI一覧 | `markdown` | [追加 04](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 複数の指標と目標を一覧にする |
| m05 | 35 | `chart_insight` | 単一チャート＋含意 | `pptx-image` | [追加 05](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 単一チャートに含意を添える |
| m06 | 36 | `stacked_bar` | 積み上げ棒 | `pptx-image` | [追加 06](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 内訳の変化を積み上げて示す |
| m07 | 37 | `waterfall` | 寄与度ブリッジ | `pptx-image` | [追加 07](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 増減の寄与を分解する |
| m08 | 38 | `true_waterfall` | 増減ブリッジ（厳密） | `pptx-image` | [追加 08](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 起点から着地を浮動棒で厳密につなぐ |
| m09 | 39 | `small_multiples` | 小図の並列比較 | `pptx-image` | [追加 09](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 同じ図法と軸で切り口を比べる |
| m10 | 40 | `comparison_table` | 選択肢の比較表 | `markdown` | [追加 10](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 選択肢を共通の評価軸で比べる |
| m11 | 41 | `scenario_table` | シナリオ比較表 | `markdown` | [追加 11](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 前提の違いと結果を並べる |
| m12 | 42 | `risk_table` | リスク一覧表 | `markdown` | [追加 12](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | リスク・兆候・対応・担当をそろえる |
| m13 | 43 | `horizontal_axis_table` | 横軸評価表 | `markdown` | [追加 13](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 横軸に並べた要件の充足を評価する |
| m14 | 44 | `heatmap_table` | ヒートマップ表 | `markdown` | [追加 14](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 交点の強弱を濃淡と文字で示す |
| m15 | 45 | `matrix_2x2` | 2×2マトリクス | `pptx-image` | [追加 15](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 二軸で位置付けを整理する |
| m16 | 46 | `process_matrix` | プロセス×観点の行列 | `markdown` | [追加 16](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 工程と観点の交点を整理する |
| m17 | 47 | `nested_row_matrix` | 入れ子行の行列 | `markdown` | [追加 17](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 大項目と下位項目を行の入れ子で示す |
| m18 | 48 | `timeline_matrix` | 時系列マトリクス | `markdown` | [追加 18](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 時期と項目を掛け合わせる |
| m19 | 49 | `theme_card_grid` | テーマカード | `markdown` | [追加 19](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 異なるテーマの問いを並べる |
| m20 | 50 | `recommendation_pillars` | 提言の柱 | `markdown` | [追加 20](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 上位提言を複数の柱に分ける |
| m21 | 51 | `numbered_imperatives` | 番号つき打ち手 | `markdown` | [追加 21](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 実行することを番号で明示する |
| m22 | 52 | `scr` | これまで・課題・対策（流れの3段） | `markdown` | [追加 22](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | これまで・課題・対策を三段で語る |
| m23 | 53 | `issue_to_solution_map` | 課題と打ち手の対応 | `pptx-image` | [追加 23](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 課題と解決策の多対多を結ぶ |
| m24 | 54 | `issue_cause_solution` | 課題→原因→解決 | `markdown` | [追加 24](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 課題から原因を経て解決へ進む |
| m25 | 55 | `issue_tree` | イシューツリー | `pptx-image` | [追加 25](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 問いを階層的に分解する |
| m26 | 56 | `current_target_state` | 現状と目指す姿 | `markdown` | [追加 26](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 現状と目指す姿の差分を示す |
| m27 | 57 | `calc_flow` | 計算ロジックの流れ | `pptx-image` | [追加 27](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 入力・式・結果の計算関係を示す |
| m28 | 58 | `process_flow` | プロセスの段階 | `markdown` | [追加 28](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 段階と各成果物を順に示す |
| m29 | 59 | `cycle` | 循環サイクル | `pptx-image` | [追加 29](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 実行と学習の循環を示す |
| m30 | 60 | `chevron_rail` | 矢羽の段階（全体像の見出し） | `markdown` | [追加 30](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 全体の進行段階を見出しにする |
| m31 | 61 | `chevron_value_chain` | バリューチェーン | `markdown` | [追加 31](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 活動の連鎖と横断支援を示す |
| m32 | 62 | `decision_fork` | 分岐と判断 | `pptx-image` | [追加 32](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 判断条件から進路を分ける |
| m33 | 63 | `roadmap` | ロードマップ | `pptx-image` | [追加 33](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 時期別の実行方針を示す |
| m34 | 64 | `gantt` | ガントチャート | `pptx-image` | [追加 34](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 期間・並行・節目を工程で示す |
| m35 | 65 | `decision_page` | 意思決定ページ | `markdown` | [追加 35](https://github.com/carnot-tech/jinba-consulting-pptx-skill/blob/e5f35e57e14d3998249a559c620a9286c95b4595/templates/freeform_parts_more_16x9.html) | 決めること・前提・依頼をそろえる |

## レイアウトを使うときの注意

- 表・比較・Q&A・入れ子行は、関係が見える表や行構造のまま使います。ヒートマップは色に加えて「高／中／低」等を併記し、ハーベイボールには凡例を置きます。
- 柱と土台は共通基盤、矢羽は順序、対向シェブロンは両側の要請、アジェンダ再掲は現在地を示します。同じ長方形であっても意味は異なります。
- カード／表の項目を増やして収まらない場合は、既存の文字を縮めず、内容を減らすかスライドを分けます。作例は主に3〜4項目に限定しています。
- 表紙 `b01` は `title`、章扉 `b04` は `section`。裏表紙 `b10` とアジェンダ再掲 `b27` は本文の構造で作り、表紙／章扉の使い回しにしていません。
- 図版22型の画像が未生成の環境では、図生成が先行依存です。原稿の完全性と画像資産のビルド完了は別々に判定します。
