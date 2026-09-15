# サバナビ（sabanavi-hikaku.com）— Claude Code 向けガイド

レンタルサーバーのASP（アフィリエイトネットワーク）比較サイト。人が読むセットアップ手順は
[README.md](README.md) を参照。このファイルは今後 Claude Code がこのリポジトリで作業する際に
知っておくべき前提・規約・注意点をまとめたもの。

## サイトの構造（重要な前提）

**ASPには料金・商品カタログを取得できるAPIが存在しない**（A8.net／バリューコマース／AccessTrade
いずれも）。そのため以下の構成になっている。

- **Googleスプレッドシートが正（source of truth）**。料金・容量・特長などは人が公式サイトを見て
  手動更新する。ASPのプログラム詳細画面に出る金額は**成果報酬額**であり、顧客向け価格ではない
  （過去に誤読しかけた実績あり。新規追加時は必ず公式サイトをWebFetch等で確認してから入力する）。
- ASPクライアント（`src/asp_clients/`）はアフィリエイトリンク取得・レポート取り込み専用。
- Jinja2 + Markdown で `public/` に静的HTMLを生成し、Cloudflare（Workers static assets、
  プロジェクト名 `sparkling-waterfall-3cf7`、独自ドメイン `sabanavi-hikaku.com`）にデプロイする。
  GitHub Actions（`.github/workflows/deploy.yml`）でmainブランチへのpush時に
  シート同期→ビルド→デプロイを自動実行する仕組みを用意済み（詳細は下記「デプロイの自動化」）。
  ただしGitHubリモート・Cloudflare API tokenの登録はユーザー側の一度きりの手作業が必要なため、
  それが未完了の間は引き続き「`public/` の中身を手動で再アップロードしてください」と伝えること。

## ビルドコマンド

```bash
# リポジトリルートで実行（-m 指定が必須。venvはこのマシンでは c:/Users/gudej/Desktop/afi/.venv）
.venv/Scripts/python.exe -m src.generate_site
```

スプレッドシートの内容を `data/services.json` に反映してからビルドする（キャッシュなので
シートを直接編集しただけではサイトに反映されない）:

```bash
.venv/Scripts/python.exe -m src.sync
```

`src/sync.py` はシート→JSON反映に加えて、`asp_name`/`asp_program_id` が入っている行があれば
対応するASPクライアント（`src/asp_clients/`）でアフィリエイトリンクの再取得も試みる
（未設定のASPは自動でスキップされるだけなので、通常のシート反映用途でもこのコマンドで問題ない）。
GitHub Actionsのデプロイワークフローもこのコマンドを使っている。

**Windows特有の注意**:
- `python`/`python3` はWindows Storeのスタブに解決されることがある。実体は
  `.venv/Scripts/python.exe`（venv化済み）。
- スクラッチのワンオフスクリプト（`from src.sheets_client import SheetsClient` 等）をリポジトリ
  ルート外から実行するときは `PYTHONPATH=c:/Users/gudej/Desktop/afi` を付けないと
  `ModuleNotFoundError: No module named 'src'` になる。`python -m src.generate_site` の形（ルート
  から `-m` 起動）ならPYTHONPATH指定は不要。
- ターミナル出力の日本語が文字化けすることがあるが、ファイル自体（Read toolで確認）やスプレッド
  シート側は正しいUTF-8。文字化けはコンソール表示だけの問題として扱ってよい。
- ビルド後は必ずローカルで `python -m http.server` を立てて主要ページ（index.html, site.js,
  style.css, reviews/*.html）が200を返すか確認してから完了報告する。

## 新しい会社を追加する手順（頻出タスク）

1. ユーザーからA8.net等のアフィリエイトリンクと公式URLをもらう。
2. **A8.netの成果報酬額を鵜呑みにしない**。WebFetchで公式サイトの料金ページを確認し、実際の
   顧客向け月額・初期費用・容量・無料SSL有無を調べる。更新後に価格が跳ね上がるキャンペーン
   価格（「初回◯%OFF」等）より、変動しない通常価格を優先的に採用する（`hidden-costs.md` 記事の
   趣旨と矛盾しないように）。
3. `config/columns.yaml` のヘッダーに合わせて、スプレッドシートに1行追加する
   （scratchpadに使い捨てスクリプトを書いて `SheetsClient.header()` → 辞書組み立て →
   `sc._ws.append_row(values)` が定番パターン）。`slug`（英数字、reviews/配下のURLになる）を
   忘れずに埋める（`diagnosis_label`列は診断ツール廃止に伴い未使用、埋めなくてよい）。
4. `data/services.json` を再生成 → `python -m src.generate_site` → HTTPスモークテスト。
5. ユーザーに再デプロイを促す。

新しい列をヘッダーに追加する場合、Googleスプレッドシートのデフォルトグリッドは26列（A〜Z）まで
なので、超える場合は `sc._ws.update_cell()` の前に `sc._ws.add_cols(n)` で列数を拡張しないと
`APIError: [400] Range (...) exceeds grid limits` になる（列数追加系のスクリプトを書くときは
毎回チェックすること）。

## データ列（`config/columns.yaml`）

`type: manual/asp/system` と `public: true/false` を持つ。主要列: `service_name`, `slug`
（内部利用、非公開）, `recommend_comment`（一言）,
`detail_review`（3〜5文の詳細レビュー、各社レビュー用ドロップダウンとreviews/個別ページで使用）,
`company`, `monthly_price`, `setup_fee`, `disk_capacity`, `transfer_capacity`, `server_type`
（「共用」「VPS」など。ソートに使う軸なので値の表記揺れに注意）, `free_ssl`,
`official_url`, `asp_name`, `affiliate_link`, `notes`（未確認事項のメモ）。
`diagnosis_label`列は診断ツール廃止（後述）により未使用（データは残っているが表示箇所なし）。

比較表のLOW/MIDDLE/HIGHプラン切り替え用に `plan_name_mid` / `monthly_price_mid` /
`setup_fee_mid` / `disk_capacity_mid` と `_high` 版も存在する（詳細は下記「比較表のプラン帯
切り替え」参照）。中位・上位プランが無い会社は空欄でよい。

新しいジャンル（サーバー以外）に展開する場合は `columns.yaml` をコピーして `genre` を変える想定
（README参照）。

## 記事内の料金・スペック表記は変数（プレースホルダー）で埋める

`content/articles/*.md` に「693円」「500GB」のように料金・スペックの数字を直接ベタ書きすると、
スプレッドシート側の価格が更新されたときに記事だけ古い値のまま取り残される（比較表・レビュー
ページは`row`から動的に出しているので自動更新されるが、記事本文はMarkdownの静的テキストのため
連動しない）。これを防ぐため、`src/generate_site.py`の`load_articles()`が記事本文をMarkdown変換
する前に **`{{種別:slug}}` / `{{種別:slug:mid}}` / `{{種別:slug:high}}`** というプレースホルダーを
`data/services.json`の該当行の値に置換する仕組みを用意してある（`resolve_placeholders()`）。

**2026-09-15時点でこの仕組みはスプレッドシートの`detail_review`/`recommend_comment`列にも適用**
している（`build()`内でrow単位に`resolve_placeholders()`を通す）。つまり各社レビュー文（Google
スプレッドシート側で編集する文章）の中で価格に触れたい場合も、`月額330円〜`のように直接タイプ
せず`月額{{price:lolipop}}円〜`と書けば、シートの`monthly_price`更新時に自動で追従する。

- 使える`種別`: `price`(→`monthly_price`), `setup_fee`, `disk`(→`disk_capacity`), `cpu_memory`,
  `plan_name`, `company`, `service_name`, `storage_type`, `backup`, `free_ssl`,
  `transfer_capacity`, `server_type`, `official_url`
- 例: `{{price:xserver}}円〜` → `693円〜`、`{{price:xserver:mid}}円({{plan_name:xserver:mid}})`
  → `1,980円(プレミアム)`、`{{disk:sakura:high}}` → `600GB`
- `price`/`setup_fee`は自動でカンマ区切り（`693` → `693`、`1980` → `1,980`）になる。他の種別は
  シートの値をそのまま文字列展開する。
- **存在しないslug、または該当プラン帯が空欄の会社を参照するとビルドがエラーで止まる**
  （意図的な仕様。サイレントに空欄・古い値を出すより、書いた本人がその場で気付ける方が安全）。
  「上位プランが無い会社」を比較記事で扱う場合は、その会社側のセルだけ地の文（「―」など）を
  書いてプレースホルダーを使わないこと。
- 値が未確認（シート側が空欄）の項目（例: 転送量が「要確認」の会社）もプレースホルダーには
  できない。その場合も従来通り「要確認(公式サイトで最新情報を確認してください)」等の地の文を書く。
- 2026-09-07時点で `xserver-vs-conoha-wing.md` / `xserver-vs-sakura.md` / `lolipop-vs-sakura.md` /
  `sakura-review.md` / `sekai-vpn-vs-millenvpn.md` の料金・スペック表をこの記法に置き換え済み。
  **新しい2社比較記事・単独レビュー記事を書く際は、料金やスペックの数字は必ずこの記法で書き、
  数字を直接タイプしない**こと（週次記事ドラフトルーティンにもこの方針を反映済み）。
- `hidden-costs.md` / `renewal-price.md` はキャンペーン価格→更新後価格という「時点の異なる2つの
  金額」を扱う記事で、スプレッドシートは現在の代表価格1つしか保持していないため、この仕組みでは
  表現できない。この2本は意図的にプレースホルダー化の対象外（今後も手動更新でよい）。

## フロントエンドの設計規約（このセッションで確立したもの）

- **ライトテーマ限定**。`prefers-color-scheme: dark` には対応しない方針（ユーザー指示）。
  `:root { color-scheme: light; }`。
- **日本語テキストに `ch` 単位を使わない**。全角文字の実測幅とズレて意図せず折り返す原因になった
  ため、`max-width` はpx指定に統一済み。短い「」引用フレーズは `.kw`（`white-space: nowrap`、
  480px以下では解除）で囲み、フレーズ途中の改行を防ぐ。
- **ボタン群は役割ごとに見た目を変える**。同じpage内に複数のボタングループが並ぶと同じ見た目では
  混同されるとフィードバックを受けた。現状の使い分け（2026-09-15のBento刷新後）:
  - `.sort-btn`（比較表ソート／プラン帯切替）: グレートレイに浮かぶセグメントコントロール
  - `.table-more-btn`（比較表もっと見る）: 点線ボーダーの控えめな全幅ボタン
  - `.tile-genre`（ホームのジャンル選択、`templates/home.html`の`.bento`内）: ジャンルの識別色
    （`--primary`/`--accent`）で塗りつぶした大きなタイル。会社数を巨大なmono数字で表示
  - `.tile-stat`（ホームの統計タイル、`.bento`内）: 白背景、ラベル＋mono数字＋補足の3段構成
  - `.tile-article`（ホームの記事カルーセル、`.article-track`内）: 固定幅260pxの白カード。
    横スクロールコンテナの中なので縦方向のtransformは使わない（色の変化のみ、上記の罠を参照）
  - `.carousel-nav`（記事カルーセルの左右移動）: 丸型ボタン、端に達すると自動でdisabled
  新しいボタン群を追加するときは、既存のどれとも視覚的に紛れないデザインを検討すること。
  （過去に存在した`.pick-chip`＝ページ上部クイックピックの番号カード、`.diag-btn`＝診断ツールの
  選択chipはいずれも役割重複・評価が低いことを理由にユーザー指示で削除済み。復活させない）
- ホバー/press feedback（transform + box-shadow）と `@media (prefers-reduced-motion: reduce)`
  対応は全インタラクティブ要素で統一して入れている。新規追加時も踏襲する。
- 各社の詳細レビュー（`.reviews`セクション）は会社数が増えてきたため、アコーディオン方式から
  `<select id="review-select">` のドロップダウンで1社ずつ表示する方式に変更済み（`.review-panel`
  を`data-slug`で出し分け）。会社が増えても縦に伸びない設計。

### 記事内のMarkdown表（`<table>`）のスタイリング

`markdown`ライブラリの`extra`拡張がそのまま出力する`<table>`は無装飾（罫線もヘッダー背景も無し）
で、比較記事の料金表などが詰まって非常に読みにくくなっていた（2026-09-15にユーザー指摘）。
`generate_site.py`の`wrap_tables_for_scroll()`が`load_articles()`/`load_pages()`の
Markdown変換直後に`<table>`を`<div class="table-scroll">`で自動的に囲み（本文側で意識する必要
なし）、`style.css`の`.article-body table`系ルールで比較表(`.compare-table`)と統一感のある見た目
（ヘッダー行に`--bg-soft`背景、行区切りは横罫線のみ・縦罫線なし、ホバーで行がハイライト）にした。
新しく記事にMarkdown表を書く際、特別な対応は不要（自動的にこのスタイルが当たる）。

### AI感を減らす（2026-09-15、ユーザー指示）

サイトを実際に見た第三者に「AIが作った感じ」「不信感」を与えないことを重視する方針。具体的には
以下を徹底する。

- **絵文字・装飾アイコンを使わない**。`templates/home.html`のジャンルカードは元々🖥/🔒等の絵文字
  アイコンを表示していたが削除し、タイトル＋件数＋矢印のみのテキストベースのカードにした
  （`favicon`の「サ」の文字ロゴのような、意味のある最小限の図形は対象外）。新しいカード/ボタンを
  追加する際も、意味を持たない絵文字での装飾は避ける。
- **実装の裏側に触れる説明文をユーザー向けコピーに書かない**。「月額料金をスプレッドシートで
  管理し」のような運営側の実装詳細（Googleスプレッドシートで一元管理している事実）は、
  ユーザーにとって比較サイトとしての信頼性を補強しないため、hero-leadやmeta descriptionからは
  削除し、「公式サイトの最新情報をもとに更新しています」という結果ベースの説明に統一した。
- **カード/枠の「枠線＋影の重ね掛け」をやめる**。1つの区切り方法（枠線 or 影 or 余白）だけを使う
  方針にした。`.genre-card`はホバー時の`box-shadow`を廃止し枠線の色変化のみに、`.diag-result-card`
  も静的な`box-shadow`を廃止し枠線のみにした。影を残すのは「本当に浮かせたいもの」（`.sort-btn.
  is-active`のような選択中インジケーター等）に限定する。未使用になった`--card-shadow`変数も削除
  済み。新しいカードを追加する際も、枠線と影を同時に付けない。
- **ブランドカラーを薄めた背景（AIが「いい感じの雰囲気」を出そうとして選びがちなパステル調の
  塗り）を避ける**。`.diagnosis`セクションの背景を`--primary-soft`（薄い青）から`--bg-soft`
  （中立なグレー）に変更した。ボタンのホバー状態や選択中の背景色など、機能的な状態を示す小面積の
  `--primary-soft`使用（`.diag-btn:hover`等）はそのままでよい——問題になるのは「セクション全体の
  雰囲気作り」として使う大面積のパステル塗りの方。
- **12px未満の文字を作らない**。`.diag-step-num`/`.diag-result-label`/`.compare-table .price
  small`/`.cell-plan-name`が0.68〜0.74rem（11px前後）だったため、サイト内の最小フォントサイズを
  0.82rem（約13px）に統一した。
- **「引き算」だけでは単調になりすぎた反省（2026-09-15）**: 上記の引き算対応後、ユーザーから
  「PRバーが無くなった分の空白が不自然」「デザイン性が皆無・単色すぎる」という指摘を受けた。
  Material Design 3（プライマリ/セカンダリ/ターシャリを役割分担して使う考え方）とSmartHR Design
  System（ブランドカラーは1つに絞りつつ、カテゴリ分け用に8色の「拡張色」を別途用意している）を
  調査し、「色を使わない」のではなく「役割の無い色を使わない」のが正しい引き算だったと整理した。
  対応: (1) `.hero`をヘッダー直下の空白のままにせず、`.diagnosis`と同じ`--bg-soft`の角丸ボックス
  にして構造を作った、(2) ジャンルカード（`.genre-card`）にジャンルごとの識別色を左ボーダーで
  付けた（`--genre-vpn: #0f766e`のように`:root`に1色ずつ追加し、`.genre-card.genre-{key}`で
  割り当てる。既存の`server`はブランドカラーの`--primary`をそのまま使用）。新しいジャンルを
  追加する際は、この左ボーダー用の識別色も追加するとよい（必須ではないが、あった方がジャンル
  カード一覧の視認性が上がる）。
  **踏んだ罠**: `.hero`をpaddingありのボックスにした際、中の`h1`/`p`がブラウザ既定の
  margin-top/margin-bottomを持ったままだったため、ボックス自身の`padding`と二重に加算されて
  上下が不自然に間延びして見えるバグを作り込んだ（ユーザーがdevtoolsで実測し指摘）。
  `.hero > :first-child { margin-top: 0; } .hero > :last-child { margin-bottom: 0; }`で解消。
  paddingを持つボックスに見出し・段落をそのまま入れる設計（Bentoタイルの中身など）を新しく
  作る際は、このパターンを毎回疑うこと（既存の`.article-body :first-child`も同じ対策）。
- **PR表示は全ページ共通のヘッダー直下バー（`.pr-bar`）をやめ、フッターの記載のみに一本化した
  （2026-09-15、ユーザー判断）**。マイベストが「広告掲載について」のような開示をフッターに集約
  しているのを参考に、`base.html`から`.pr-bar`要素を削除し、CSSの`.pr-bar`/`.pr-bar-inner`/
  `.pr-label`ルールも不要になったため削除済み。フッター文言は「本サイトはPR(アフィリエイト広告)
  を含みます。紹介する商品・サービスの一部にはアフィリエイトリンクを使用しており、リンク経由の
  申し込みにより成果報酬を受け取る場合があります。」に強化し、`disclaimer`ページ（【広告に関する
  表示】の章を含む）への導線もそのまま残した。**留意点**: ステマ規制（景品表示法、2023年10月
  施行）は「一見して広告とわかること」を求めており、比較表・レビューという「個別の推奨コンテンツ」
  がファーストビューでPRと分かる状態ではなくなった分、ヘッダー上部に常設バーを置く場合よりは
  リスクが上がるトレードオフがあることを認識した上での選択。今後、比較表のCTA付近など「実際に
  商品を薦めている箇所」に個別のPR表記を足す方向（価格.com方式）も検討候補として残しておく。

### `hidden` 属性とCSSの `display` 競合に注意（このセッションで2回踏んだ罠）

JSで `element.hidden = true` を使って要素を隠す設計を多用しているが、そのクラスに
`.foo { display: flex/grid/block; ... }` のような**セレクタ全体に効く** `display` 指定が
CSSにあると、ブラウザのUAスタイル `[hidden]{display:none}` より **author スタイルが優先される**
ため、`hidden` を立てても実際には隠れない（specificityの問題ではなく、UA起源よりauthor起源が
常に勝つカスケードの仕様）。過去に `.diag-buttons`（`display:flex`）と `.table-more-btn`
（`display:flex`）、`.compare-table tr`（モバイル幅で`display:block`）で実際にバグを踏んだ。

**対策**: `display` を明示的に指定しているクラスをJSの `hidden` トグル対象にする場合は、必ず
`.foo[hidden] { display: none; }` のような属性セレクタ付きの上書きルールを追加する
（`[class][hidden]`の形は素の`.foo`よりspecificityが高いので、これだけで安全に上書きできる）。
迷ったら、新しく「JSでhidden制御する要素」を作るたびにこのパターンを疑うこと。

### 「サバナビ2026」デザイン刷新（2026-09-15）

現行の構成を無視して2026年のWebデザイントレンド（Bento UI・大胆なタイポグラフィ・
マイクロインタラクション）を取り入れたコンセプト案をArtifact（`サバナビ2026`）として提示し、
ユーザー承認を得たうえで実サイトに実装した。コンセプトは「比較を計器のように読ませる」
——レンタルサーバー/VPNという題材を、パッチパネル/計器盤のメタファーで表現している。

- **配色トークン刷新**（`style.css`の`:root`）: 紙のようなグレー地`--bg:#f4f5f0`の上に
  白のパネル`--card-bg:#fff`を置く構成に変更。`--primary`を紺(#1e3a8a)から信号のような
  ブルー`#1b4dff`に、`--accent`を`#ea580c`からアンバー`#ff8a1e`に変更（`--accent-fg`も
  白から濃いインク色`#241505`に変更——新しいアンバーは明るいため白文字だとコントラスト不足）。
  `--genre-vpn`という別トークンは廃止し、VPNジャンルは`--accent`をそのまま使う設計に統一
  （`.tile-genre.genre-{key}`で`--primary`/`--accent`のどちらかを割り当てる）。
  `body`に方眼紙のような薄いグリッド背景（`background-image`の2重`linear-gradient`）を追加。
- **フォント3役化**: 見出し用に`--font-display`（Big Shoulders Display、太い条件付き
  ディスプレイ書体）、データ用に`--font-mono`（IBM Plex Mono、`font-variant-numeric:
  tabular-nums`と併用）を追加。`h1`/`.site-title`は`--font-display`、価格・日付・件数などの
  数字類（`.compare-table .price`, `.diag-result-price`, `.summary-value`,
  `.updated-at`, `.article-list .date`等）は`--font-mono`を適用。本文は従来通りNoto Sans JP。
  `base.html`のGoogle FontsリンクにBig Shoulders DisplayとIBM Plex Monoを追加済み。
- **トップページ（`home.html`）をBentoグリッド化**: `.bento`（12列グリッド、`gap:1px`を
  `--border`色で埋めることでパッチパネルの継ぎ目のように見せる）の中に、ジャンルタイル
  （`.tile-genre`、色面塗り＋会社数の巨大な数字＋会社名サンプル）、統計タイル（`.tile-stat`、
  掲載社数・最安値帯・価格帯比較を`generate_site.py`側で動的計算——**ハードコードした事実を
  置かない**のがこのサイトの一貫した方針、上記「記事内の料金・スペック表記」参照）、記事タイル
  （`.tile-article`、他と違い角丸12pxで「編集エリア」として質感を分けている）を並べている。
  `generate_site.py`の`build()`で`genre_samples`（ジャンルごとの会社名サンプル）・
  `total_count`・`cheapest_row`（全社中の最安値行）を計算し`home_tpl.render()`に渡している。
- **`.hero`/`.diagnosis`を白パネル化**: 旧デザインの「グレー背景の角丸ボックス」から、
  白背景＋`--border`の1pxボーダー（角丸4px、計器盤らしいシャープな角）に変更。
  ページ全体が紙色地になった分、パネル類は白で浮かせる構成に統一した。
- **`.hero`の白い箱を廃止（2026-09-15、実装直後にユーザー指摘で修正）**:
  最初の実装では`.hero`を白背景＋ボーダーの角丸パネルにしていたが、ユーザーから
  ホームのヒーロー（方眼紙の地に直接文字を置いた見た目）は良い、比較表ページの白い箱は
  「悪さをしている」との指摘を受け、**白背景を廃止し、方眼紙の地に直接置く**形に統一した。
  `.hero`は完全に無地（margin のみ）——「白い角丸カードを積み重ねる」という直しにくいAI感のある
  パターンに戻らないようにしている。白パネル（`--card-bg`背景＋ボーダー）を使ってよいのは、
  Bentoタイルのような、**単一の要素として意味的に独立しているもの**に限定する方針。セクション
  全体を囲むラッパーとしては使わない（同じ理由で、当時あった`.diagnosis`セクションも上下の
  1本線だけでゾーンを示す形に修正していたが、診断ツール自体が後日廃止されたため今は存在しない）。
- **お役立ち記事を独立したグループに分離（2026-09-15、実装直後にユーザー指摘で修正）**:
  最初の実装では記事タイルもジャンル/統計タイルと同じ`.bento`（1pxの継ぎ目でつながった1つの
  グリッド）の中に入れていたが、ユーザーから「統計欄との間はグループ自体が分かれているように
  見せたい」との指摘を受け、`.bento`（ジャンル＋統計タイルのみ）と`.articles-panel`（記事タイル、
  独立した`<section>`＋通常の見出し）を完全に別の要素に分離した。記事カードは継ぎ目トリック
  （コンテナ背景色を`--border`にして`gap`で線を作る手法）を使わず、`.article-grid`に
  `gap: 5px`を指定するだけのシンプルな構成にした（`.tile-article`自体にはmarginを持たせない
  ——`gap`とmarginを両方使うと隙間が二重に加算されるとユーザーから指摘があったため）。
  分離した直後、記事カードの白背景が見えなくなり「デザインが崩れた」と指摘を受けたが、原因は
  CSSが外れたことではなく（`.tile`/`--card-bg`は正しく適用されていた）、`--card-bg`(#fff)と
  ページ全体の地の色`--bg`(#f4f5f0)の明度差が小さすぎて、方眼紙の罫線が無いカード内側では
  白カードと地の境界がほぼ見分けられなかったこと。`.article-grid`自体に`--bg-soft`の背景＋
  `padding:5px`を追加し、bentoの継ぎ目と同じ発想で「白カードがグレーのトレイに乗っている」
  構図にしてコントラストを作った。
- **お役立ち記事を横スクロールカルーセル化（2026-09-15）**: 4列グリッドだと記事数が増えたとき
  ／タイトルが長いときにレイアウトが崩れる懸念があったため、ユーザーから他サイトのカルーセルUI
  （固定幅カード＋左右の丸ボタン）を参考例として共有され、それに合わせて実装した。
  `home.html`の`.article-carousel`は「◀ボタン（`data-carousel-prev`）＋横スクロールする
  `.article-track`（`data-carousel-track`）＋▶ボタン（`data-carousel-next`）」の3分割。
  `.tile-article`は`flex: 0 0 260px`の固定幅、`.article-track`は`overflow-x:auto`+
  `scroll-snap-type:x mandatory`。ボタンのクリックは`site.js`の`scrollBy()`で1カード分
  （カード幅+gap）ずつスクロールし、スクロール端に達したら該当ボタンを`disabled`にする
  （`prefers-reduced-motion`時は`scroll-behavior:auto`でアニメーションを止める）。
  表示件数を`articles[:4]`→`articles[:8]`に増やした（カルーセルなので画面幅内に収める必要が
  なくなったため）。新しいジャンルを追加してもこの仕組みは変更不要。
  トレイの背景（`--bg-soft`）は左右の移動ボタンも含めた`.article-carousel`全体に付けている
  （`.article-track`だけに付けると、ボタンだけ地の色から浮いて見えるとユーザーから指摘があった
  ため修正）。
  **踏んだ罠**: `.tile-article:hover`に他のカード群と同じ`transform: translateY(-2px)`の
  浮き上がりを付けていたが、`.article-track`が横スクロール用に`overflow-x: auto`を持つと
  `overflow-y`も自動的に`auto`になる仕様（CSSの標準挙動）のため、縦方向の浮き上がりが
  クリップされたりトレイの外にはみ出して見えたりする不具合になった（paddingを増やしても
  スクロールコンテナ自体の境界は変わらないので直らない）。**横スクロールするコンテナの中の
  カードには、縦方向のtransform（浮き上がり演出）を使わない**——色の変化だけにする。
  **自動スライド**: 5秒間隔で1カードずつ自動送りし、末尾まで行ったら先頭へ戻る。ただし
  「読もうとしている最中に中身が変わる」不快さ（上記の参考記事でも指摘されていた実例）を避ける
  ため、カルーセルにマウスオーバー／キーボードフォーカス中は一時停止する（ユーザーが3択の中から
  この仕様を選択）。`prefers-reduced-motion`時は自動送り自体を開始しない。
- **今回のスコープ**: トップページは完全にコンセプト通り刷新。比較表ページ（`index.html`）・
  レビューページ（`review.html`）・記事ページ（`article.html`）・固定ページ（`page.html`）は
  構造は変えず、上記の配色トークン・フォントの変更を通じて自動的に見た目を統一している
  （このサイトがほぼ全面的にCSS変数経由で色を参照する設計だったため、トークンの変更だけで
  サイト全体の配色が連動して変わった）。コーナーの丸み（instrument系はシャープ、editorial系は
  やや丸め）を各コンポーネントに作り込む作業や、比較表・レビューページ自体のレイアウトを
  Bento的に再構成する作業は今回は行っていない——ユーザーから追加の修正依頼があれば都度対応する
  想定。

### デザイン変更時の進め方（2026-09-15、ユーザー指示）

見た目に関する変更（配色・レイアウト・コンポーネントデザイン等）を行う際は、自己流で決め打ち
せず、Web検索等でWebデザインのトレンド・有名企業が公開しているデザインシステム/スタイルガイド
（例: Material Design、SmartHR Design System等）を調査したうえで、根拠を持って適応する方針。
2026-09-15時点でMaterial Design 3のカラーロール（プライマリ/セカンダリ/ターシャリの役割分担）と
SmartHR Design System（ブランドカラー1色＋カテゴリ分け用の拡張色という構成）を参考に、ジャンル
カードの識別色を導入した実績がある（上記「AI感を減らす」参照）。

## 診断ツールは廃止済み（2026-09-15）

以前は`.diagnosis`（STEP1〜3の質問に答えると1社をおすすめする機能）が`templates/index.html`
（`genre_key == "server"`限定）にあったが、「サバナビ2026」デザイン刷新後に見た目が崩れたこと、
および診断の中身自体もユーザーの評価が高くなかったことから、ユーザー指示で丸ごと削除した。
`templates/index.html`の`.diagnosis`セクション、`style.css`の`.diagnosis`/`.diag-*`一式、
`site.js`のSTEP1〜3・結果パネルのロジックをすべて削除済み。スプレッドシートの`diagnosis_label`
列（診断ツールのボタン文言用）は今はどこにも表示されない**未使用列**として残っている
（列自体は削除していない。今後別の用途に転用するか、不要なら手動で削除してよい）。
同種の「質問に答えると1社に絞り込む」機能を再度作る場合も、今回の経緯（デザインの複雑さの
わりに評価が低かった）を踏まえて、本当に必要か一度検討すること。

## 比較表のスケール対策

社数が増えると比較表が縦に伸びすぎる問題への対応として、初期表示は上位3社のみ
（`.table-more-btn` クリックで全社表示、data-limit属性で件数を制御）。ボタンは開閉トグル式
（`tableExpanded` フラグ、展開中は「閉じる」表示、再度押すと上位3社に戻ってスクロール位置も
テーブル先頭に戻す）。JSが動かない場合は全社表示のままになるprogressive enhancement
（`hidden` はJSが後から付与する）。

## 比較表のプラン帯切り替え（LOW/MIDDLE/HIGH）

各社、入門プランだけでなく中位・上位プランの料金も比較できる機能を実装済み（1行=1会社という
データモデルは崩していない）。

- **スキーマ**: `monthly_price` / `setup_fee` / `disk_capacity` が「LOW（入門）」を表す既存列。
  同じ意味の列を `_mid` / `_high` サフィックス付きで追加（`plan_name_mid`, `monthly_price_mid`,
  `setup_fee_mid`, `disk_capacity_mid` と `_high` 版）。中位・上位プランが存在しない会社
  （例: お名前.comは1プランのみ）はこれらを空欄のままにしてよい —— テンプレート側が
  `monthly_price_{tier}` の有無で「そのプランが存在するか」を判定し、無ければ price/spec
  セルとも「―」表示にする（`index.html` の比較表ループを参照）。
- **表示**: 各セル（月額料金・スペック）は3つの `.tier-variant[data-tier]` を重ねて出力し、
  選択中のtier以外を`hidden`にする方式。`<tr>` には `data-price-low/mid/high` /
  `data-disk-low/mid/high` を持たせておき、tier切り替え時にJSが `data-price` / `data-disk`
  （ソート機能が参照する属性）を選択中tierの値に差し替えてから `sortRows()` を再実行する
  （`site.js` の `#tier-toolbar` クリックハンドラ）。
- **データ収集の考え方**: 各社の「もう1〜2段階上のプラン」を公式サイトで確認し、キャンペーン
  価格かどうかより「同じ会社の実在するプラン名・価格・容量」であることを優先。全社が綺麗に3段
  持っているわけではない（ロリポップ・さくらはMIDのみ、お名前.comはLOWのみ）ため、無理に埋めず
  空欄＝「―」表示を許容する設計にしてある。会社を追加する際、MID/HIGHの調査は必須ではなく
  任意（無くてもサイトは壊れない）。

## 価格の月次チェック（半自動運用）

完全自動での価格取得・反映はしない方針（スクレイピングの壊れやすさ、AI要約のブレ、
キャンペーン価格を誤って拾うリスクがあるため）。代わりに `python -m src.price_check_report`
を実行すると、掲載中の全社の「確認URL・現在の記録価格(LOW/MID/HIGH)・アフィリエイトリンク」を
`PRICE_CHECK.md`（リポジトリ直下）にMarkdown表として出力する。ユーザーが月1回これを見ながら
各社の公式サイトと記録価格を見比べ、ズレていればスプレッドシートを更新する運用。
このスクリプトは差分検知はしない（あくまで「どこを見ればいいか」の一覧化のみ）。

## SEO対策

「見つけてもらう」ことを目下の最重要課題として、以下を実施済み・方針として採用している。

- **favicon**: `templates/favicon.svg` / `favicon.ico` / `favicon-16x16.png` /
  `favicon-32x32.png` / `apple-touch-icon.png` を設置し、`base.html` から参照。ブランドカラー
  （`--primary: #1e3a8a`）の角丸スクエアに「サ」の白抜き1文字という最小限のデザイン。
  生成には Pillow を使用（`.venv` にインストール済み。Yu Gothic Bold で「サ」を描画）。
  ソーススクリプトは使い捨てでscratchpadに置いたのみでリポジトリには残していない
  ——デザインを変える場合は同じ要領（PILで角丸背景＋中央にテキスト描画）で作り直せばよい。
  `generate_site.py` の `build()`内でstyle.css/site.jsと同様に `public/` へコピーしている。
- **構造化データ（JSON-LD）**: `base.html` に `{% block structured_data %}` を用意し、
  全ページ共通で `WebSite` を出力。各テンプレートがこのブロックで追加:
  - `index.html`: `FAQPage`（比較表ページのよくある質問4件と対応、リッチリザルト狙い）
  - `review.html`: `BreadcrumbList`（比較表 → 各社名）
  - `article.html`: `Article`（headline/datePublished/author/publisher）+ `BreadcrumbList`
  実装時の注意: Jinja2の `autoescape=True` のままJSON文字列を手組みすると `"` などが
  HTMLエンティティ化されて`<script type="application/ld+json">`内でJSONとして壊れるため、
  必ず `{% set foo = {...} %}` でdictを組んでから **`{{ foo | tojson }}`** で出力すること
  （生の`{{ }}`展開でJSON文字列を作らない）。`site_url`（`SITE_BASE_URL`）は
  `generate_site.py`の全`render()`呼び出しに渡すよう揃えてある。
- **コンテンツ戦略**: 「レンタルサーバー比較」のような一般的な語で新規ドメインが早期に上位表示
  されるのは現実的に難しいため、競合が薄いロングテールキーワードでの流入を優先する方針。
  具体的に効率が良いパターンとして、**2社の直接比較記事**（例:
  `content/articles/xserver-vs-conoha-wing.md`、「A社 B社 比較」のような検索意図に直接刺さる）
  を追加した。この形式は `data/services.json` に既にある実データ（料金・容量・特長）をそのまま
  使えるため新規のファクトチェックがほぼ不要で、比較的低コストに量産できる。今後も
  検索されやすそうな2社の組み合わせ（例: 知名度の近い会社同士、価格帯が近い会社同士）があれば
  同じ形式で追加するとよい。新しい記事はトップページの`.more-articles-grid`にも1件追加リンクを
  置くと内部リンクとして機能する（`article_index.html`の一覧は`content/articles/*.md`から自動生成
  されるので手動追加不要）。
- **各社レビュー（`detail_review`）の深堀り（2026-09-15開始）**: サイトが3週間前後と新しく
  アクセスがほぼ無い状況について、一般的なSEOの目安（新規ドメインは3〜6ヶ月の「サンドボックス」
  期間が普通）に照らせば想定内という調査結果をユーザーと共有した上で、ユーザーから「各社レビューを
  伸ばす」「詳しい人でも知らない知識を入れる」方針の指示を受けて着手。各社の公式サイトをWebFetchで
  深掘りし、単なる言い換えでなく独自の技術仕様（サーバーソフトウェア、PHP対応バージョン、SSH/Git/
  WP-CLI対応、コントロールパネルの種類、データセンター所在地、サポート体制の詳細、最新のアップデート
  情報など）を追加する形で`detail_review`を400〜600字程度に拡充する運用。Agent（`general-purpose`）
  を1社1エージェントで並列起動し、WebFetch優先・不可の場合はWebSearchで代替、確認できない情報は
  書かない（創作禁止）という条件で調査・ドラフトさせ、内容を確認してからスプレッドシートに反映する
  進め方が機能した。2026-09-15時点で xserver / sakura / lolipop / conoha-wing / mixhost / onamae /
  sekai-vpn の7社が完了（Search Consoleで表示回数がある会社を優先）。残り13社
  （conoha-vps, colorfulbox, onamae-vps, xserver-vps, shin-vps, millenvpn, sakura-vps,
  sakura-vps-windows, kagoya-vps, starserver, heteml, glocal-vpn-fixed-ip, glocal-vpn-movie）は
  同じ要領で継続予定。価格に触れる場合は直接ベタ書きせず`{{price:slug}}`プレースホルダーを使うこと
  （上記「記事内の料金・スペック表記は変数（プレースホルダー）で埋める」参照、2026-09-15時点で
  `detail_review`もプレースホルダー解決の対象）。
- **今後の候補（未着手）**: 被リンク獲得。

## 外部プラットフォーム（note/Zenn）での拡散（2026-08-27調査、2026-09-01時点で投稿済み）

サイトへの送客チャネルとしてnote.com/Zennでの記事投稿を検討し、規約を調査した。結論：
**Zennは見送り、noteのみ検討する。**

- **Zenn**: 2025年6月の規約改定で「SEOまたはアフィリエイトを目的とする投稿」が明示的に禁止対象
  に追加された（コミュニティガイドラインにも「宣伝は記事末尾の固定メッセージ程度」と明記）。
  「客観的に」判断されるため、書き方を工夫しても、比較サイトへの送客が目的と読み取れれば違反
  になり得る。サバナビは構造上アフィリエイト収益が目的の比較サイトなので、送客記事はほぼ定義上
  この禁止行為に該当する。読者層（エンジニア）も共用レンタルサーバー比較とは噛み合いにくい。
  → **サバナビの送客目的では使わない方針。**
- **note**: 規約上アフィリエイトリンクを全面禁止してはおらず、「PR」等の開示表記があれば認められる
  運用（サバナビ本体の`.pr-bar`と同じステマ規制対応の発想でそのまま運用できる）。読者層も一般消費者
  寄りでこのサイトの内容と噛み合う。ただしnoteからのリンクはnofollowのため、被リンクによる直接的な
  SEO効果はほぼ無い。効果があるとすれば「記事経由でクリックしてもらう」導線としての価値のみ。
- **自動化について**: 別プロジェクトでZenn向けの自動投稿パイプライン（Claude Codeの定期Routine、
  Zennの GitHub連携を利用）を構築し記事1本を公開できた実績はあるが、GitHub連携の仕組みなので
  note（公式の投稿APIが存在しない）にはそのまま転用できない。そのRoutineが最終的に詰まった
  「クラウドセッションから直接GitHubへpushする際の403エラー」は、このリポジトリの
  `seo-report.yml`のように**GitHub Actions自身にpushさせる方式なら回避できる**ことは実証済み
  だが、note投稿自体を無人化する経路が無い以上ここでは使えない。
- **推奨する進め方（未着手）**: いきなり自動化・定期投稿にはせず、Claudeが下書きを1本書き、
  ユーザーが確認のうえ手動でnoteに投稿し、実際にサバナビへのクリックが発生するか様子を見てから
  継続するかどうかを判断する（価格の月次チェック・SEOレポート自動化と同じ「まず手動で効果検証
  してから自動化を検討する」進め方）。ネタは`data/services.json`の既存データがそのまま使える
  「レンタルサーバーの選び方」寄りの一般向け記事が、追加のファクトチェックが少なく効率的。

## SEOレポートの自動生成（Search Console + Cloudflare Web Analytics）

稼働中。Google Search ConsoleとCloudflare Web Analyticsは両方ともAPIで自動取得しており、
毎月3日10:00(JST)にGitHub Actions（`.github/workflows/seo-report.yml`）が
`python -m src.seo_report`（`src/seo_report.py`）を実行し、検索クエリ・検索流入ページ・
ページ別アクセス数を `SEO_REPORT.md` に自動コミットする。ユーザーが手動でダッシュボードを
確認してスクリーンショットを共有する必要はない。

- **Search Console側**: 新規サービスアカウントは作らず、スプレッドシート用の既存サービスアカウント
  （`sheetsapi@avian-outrider-506621-i4.iam.gserviceaccount.com`）を流用。Search Console側で
  「設定 > ユーザーと権限」からこのアカウントに閲覧権限を付与済み（ユーザーの一度きりの操作、
  Claude Codeからは実行不可）。GCP側では `searchconsole.googleapis.com` を有効化済み。
  APIはWebmasters API（`https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query`）
  を`google-auth`の`AuthorizedSession`で直接叩く方式（`google-api-python-client`は追加していない）。
  scopeは`https://www.googleapis.com/auth/webmasters.readonly`。
- **Cloudflare側**: デプロイ用の`CLOUDFLARE_API_TOKEN`とは別に、Analytics: Read権限のみを持つ
  閲覧専用トークン（`CLOUDFLARE_ANALYTICS_TOKEN`）を新規発行して使う
  （デプロイ用トークンを誤って触って壊すリスクを避けるため、意図的に分離）。
  ページ別アクセス数はGraphQL Analytics APIの `rumPageloadEventsAdaptiveGroups`
  （アカウントスコープ、`accountTag`でフィルタ。`siteTag`指定は今のところ不要だった）を使用。
  `CLOUDFLARE_ACCOUNT_ID`はデプロイworkflowと共通の値を再利用。
- ローカルでテストする場合は `.env` に `CLOUDFLARE_ANALYTICS_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` を
  追加してから `python -m src.seo_report` を実行する（`.env.example`に項目あり）。
- レポートは自動生成のみで、そこから記事を書く・企業を追加するといった判断は自動化していない
  （意図的。価格の月次チェックと同じ「材料を揃えるところまでを自動化する」設計思想）。
  クラウドの定期実行エージェント（`https://claude.ai/code/routines/trig_01EpJFBzMjaKRSw7BKy59FFX`）が
  `SEO_REPORT.md`と現在のコンテンツラインナップを突き合わせて次の一手を提案する運用。

## デプロイの自動化（GitHub Actions → Cloudflare Workers）

稼働中。GitHubリポジトリ `https://github.com/afiwork-arch/Afi`（ブランチ`main`）にpushすると、
`.github/workflows/deploy.yml` が `python -m src.sync`（シート→JSON同期）→
`python -m src.generate_site`（ビルド）→ `cloudflare/wrangler-action@v3` での
`wrangler deploy`（デプロイ）を自動実行する。デプロイ対象は `wrangler.toml`
（`name = "sparkling-waterfall-3cf7"`, `[assets] directory = "./public"`）で指定済み。
GitHubリポジトリのSecretsに `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` /
`GOOGLE_SERVICE_ACCOUNT_JSON`（ファイルの中身） / `GOOGLE_SHEET_ID` /
`GOOGLE_SHEET_WORKSHEET_NAME` を登録済み。`gh auth status` で認証済み（`gh run watch`
で実行中のワークフローを直接監視できる）。もう「`public/` を手動アップロードしてください」と
案内する必要はない —— コードやコンテンツの変更は `git add` → `git commit` → `git push` で
自動的に本番へ反映される。

**wrangler.toml の `html_handling` はデフォルト（未指定）のままにすること**。
`"none"` にすると `.html` 拡張子への307リダイレクトは消えるが、代わりに
`/`（ルート）や `/articles/` のようなディレクトリ配下の `index.html` 自動解決も
一緒に無効化されトップページが404になる（一度実際に起きた）。

**サイト内の内部リンクは拡張子なしURL（例: `articles/hidden-costs`）に統一済み**
（2026-09-01対応）。以前は`.html`付きで書かれており、リダイレクト経由になるだけでなく、
`index.html`部分のroot相対パス計算にバグがあり**VPNページ（`/vpn/`）の比較表から各社詳細
レビューへのリンクが実質404になっていた**（サーバー系ページでは偶然壊れず気づかれなかった）。
修正時は`wrangler dev --local`でCloudflareの実配信挙動（拡張子なしURLの解決・`.html`への
307リダイレクト）をローカル再現して検証すること（`python -m http.server`では拡張子なし
URLの解決を再現できないため不十分）。新しいテンプレート/記事を書く際も、内部リンクは
拡張子なし・`{{ root }}`プレフィックス付きで書く（`templates/base.html`等を参照）。

## 週次記事ドラフト・企業候補追加ルーティン（Claude Code Remote）

稼働中。クラウドの定期Routine「サバナビ 週次記事ドラフト」（毎週月曜10:00 JST）が2つのことを行う。

- **A. 記事ドラフト**: SEO_REPORT.md・CLAUDE.mdのコンテンツ戦略・既存記事一覧を見て次の1本の
  テーマを決め、記事を書く。**mainには直接コミットせず、`article-draft-YYYY-MM-DD`ブランチに
  push → `gh pr create`でPRを作成**して終了する（マージ・強制pushは行わない）。ユーザーが
  PRを確認し、問題なければClaude Codeに伝えてマージ・デプロイする。
- **B. 企業候補追加**: RECOMMENDED_COMPANIES.mdに未掲載候補をWebSearchで調査して追記し、
  **mainへ直接commit・push**する（現在申請中の企業が無いため、追加自体はどんどんやってよい方針）。

**なぜAとBで扱いが違うか**: Aは公開されるとサイトの内容そのものになるため人のレビューを挟む。
Bは`RECOMMENDED_COMPANIES.md`の追記のみでサイトのビルドには一切影響しない（ユーザーが
ASP側で申請するかどうかの判断材料が増えるだけ）ため、レビュー無しで直接反映して問題ない。

**Aを「回答内にテキスト提示するだけ」にしていた初期設計をやめた理由**: クラウドRoutineの
出力ファイルは`SendUserFile`でユーザーのclaude.aiアカウント（ルーティンの実行セッション
ページ）に直接届き、Claude Codeの通常チャットには入ってこない。長文の日本語をユーザーが
そこからコピー&ペーストでこのチャットに転送しようとしたところ、**UTF-8の各文字の一部
バイト（制御文字範囲0x80〜0x9F）が経路のどこかで欠落し、プログラム的に復元不可能な文字化け**
が発生した（単なるエンコーディングのズレではなく情報が失われるため、latin-1/cp1252等での
再デコードでは直せない）。ブランチ+PR方式なら、Gitがそのまま正しいUTF-8で運んでくれるため
この問題自体が起きない。

**環境の既知の制約**:
- クラウドRoutineの環境では**WebFetchが常にブロックされる**（`EGRESS_BLOCKED`、
  `google.com`宛てですら失敗する）。WebSearchは使えるが、公式サイトへの直接アクセスによる
  一次情報確認はできない。そのためBの候補企業情報はWebSearchのスニペットのみに基づくもので、
  **ASP申請前に必ずユーザー自身が公式サイトで再確認する**運用にしている。
- クラウドRoutineからのGitHub pushには**組織管理者によるClaude GitHub Appのインストール/
  再連携**が必要（`https://github.com/apps/claude/installations/select_target` または
  `https://claude.ai/customize/connectors?auth_start=github&auth_start_force=1`）。
  未設定だと`403 Claude doesn't have GitHub access to ...`で失敗する。2026-09-01に
  この対応を行い解消済みだが、権限が外れた場合は同じ現象が再発しうる。

## トップページ（ハブページ）とジャンルのURL構成

**2026-09-15に構成変更**: 以前は `server` ジャンルの `path` が `""`（空文字）で、トップページ
（`/`）自体がレンタルサーバー比較表になっていた。ユーザーから「ジャンルが今後増える前提で、
トップページはジャンル選択のハブにして、比較表は各ジャンル配下に置きたい」という要望を受け、
**開設から3週間程度でGoogleの評価がほぼ付いていない今のタイミングが変更コストが一番低い**
という判断のもと、以下の構成に変更した。

- `/`（`templates/home.html`）が**ジャンル横断のハブページ**。ジャンルカード（`genres`から
  自動生成、アイコンはJinja側で`genre_key`ごとに手動対応——`config/columns.yaml`にアイコン用の
  列は無い）と、直近記事のカード一覧（`articles[:6]`、日付降順の自動抽出なので手動更新不要）を
  表示する。
- レンタルサーバー比較表は `/server/`、VPN比較表は `/vpn/`（`config/columns.yaml`の
  `genres[].path` が両方とも空でない値になった）。
- **アーキテクチャ**: 別ジャンル用に別リポジトリ/別ドメインを作るのではなく、**同じサイト・同じ
  スプレッドシート内で複数ジャンルを扱う**設計にしてある（1つのドメインに検索の信頼・被リンクを
  集約したほうが新規ドメインを増やすより効率的という判断。ユーザーもサイト名変更を許容している）。
- `generate_site.py` の `build()` が `genres` の数だけ比較ページを生成する
  （`path: "server/"` → `public/server/index.html`、`path: "vpn/"` → `public/vpn/index.html`）。
  トップページのハブは`genres`とは別に`build()`内で明示的にレンダリングしている。
  ナビ（`base.html`）・sitemap・パンくずJSON-LD（`review.html`/`article.html`）はすべて
  `genres` リスト駆動なので、ジャンルを追加すればこれらは自動的に追従する。
- **稼働中のジャンル**: `server`（レンタルサーバー/VPS、`/server/`）、`vpn`（VPN、`/vpn/`。
  2026-08-27公開）。`templates/index.html`（各ジャンルの比較表ページ本体）は全編
  `{% if genre_key == "server" %}...{% else %}...{% endif %}` で分岐している（hero-lead/intro/
  tier-toolbar(serverのみ)/比較表のスペック列・無料SSL列(serverのみ)/
  FAQ+そのJSON-LD/もっと詳しく知りたい方へ）。VPNのような「容量・CPU・無料SSL・自動バックアップ」
  の概念が無いジャンルでは、比較表からその列自体を非表示にしている（データが無いのに列だけ残して
  「―」を並べるより誠実という判断）。
- **新ジャンルを追加する手順**:
  1. `templates/index.html` の `genre_key` 分岐に、そのジャンル向けの `{% elif %}` 分岐を足す
     （hero-lead/intro/FAQ文言、比較表に出す列が他ジャンルと違うならそこも）—— ここが唯一
     「genresリストに足すだけでは終わらない」部分。分岐を追加せずに公開すると、既存ジャンルの
     文言がそのまま出てしまう。
  2. `templates/home.html` のジャンルアイコン分岐（`{% if g.key == "server" %}...{% elif %}`）
     にもアイコンを追加する（無くてもビルドは通るが📦のデフォルト絵文字になる）。
  3. `config/columns.yaml` の `genres` リストに新しいエントリを追加（`path`は必ず末尾スラッシュ
     付きの空でない文字列にする）
  4. スプレッドシートの新規行に該当する `genre` 値を設定
  5. そのジャンル向けの比較記事・レビューを追加（任意）

**この変更で踏んだ罠（次に同じ変更をするときのために記録）**: `templates/index.html`の
`{% if genre_key == "server" %}` 分岐内には、`href="articles/xxx"` のように **`{{ root }}`
プレフィックス無しのハードコードされた内部リンクが多数残っていた**（サーバーが元々ルート直下
`path: ""` だったため、`root=""`と一致してたまたま動いていた）。VPN側の分岐は`{{ root }}`を
律儀に付けていたため気づかれずに残っていた。サーバーを`/server/`に動かした瞬間、これらのリンクは
すべて壊れる（`{{ root }}`無しの相対リンクは`/server/`から見た相対パスとして解決されるため）。
**「ジャンルの`path`を将来変える可能性がある分岐（`{% if genre_key == "xxx" %}`）の中では、
内部リンクに必ず`{{ root }}`を付ける」を徹底すること**。`content/articles/*.md`側にも
`[比較表](../index)`のように「サーバーがルート直下にある」前提の相対リンクが12ファイル・
16箇所残っていたため、`../server/`に一括置換した（記事は常に`/articles/`配下なので`root`
プレフィックス問題は起きないが、リンク先のパス自体が変わる点に注意）。

**おすすめ企業リスト（`RECOMMENDED_COMPANIES.md`）**: まだアフィリエイトリンクが無い追加候補の
企業を一覧化したファイル。Claude Codeが調査（公式サイトURLを確認済みのもの）のうえで追記し、
ユーザーがASP側で申請してリンクを共有したら、スプレッドシートに反映してこのリストから削除する
という運用（ファイル冒頭に運用フローを明記済み）。新しい会社を追加する作業（記事追加、ジャンル
横展開など）のたびに、このファイルの内容も見直して更新すること。

## コンプライアンス

- ステマ規制（景品表示法、2023年10月施行）対応で `base.html` にPR表示バー（`.pr-bar`）を常設。
- `content/pages/` に運営者情報・プライバシーポリシー・免責事項・お問い合わせを設置済み。
- 比較表脚注に「キャンペーン価格を含む場合がある」旨の打ち消し表示あり。新しい会社を追加する際も
  この表現と矛盾しない価格の選び方をする（上記「新しい会社を追加する手順」参照）。

## 既知の未確認事項

- mixhostの初期費用が未確認。
- xserver / conoha-wing / mixhost / lolipop / onamae / conoha-vps / colorfulbox の
  `transfer_capacity`（転送量）が未確認（`notes` 列に記載あり）。さくらのみ「無制限」を確認済み。
- xserver-vps / shin-vps / sakura-vps / sakura-vps-windows / kagoya-vps の転送量・
  バックアップ有無が未確認（xserver-vpsはビジネスプランのみ自動バックアップ○表記を確認済み、
  それ以外のプランは未確認）。
- **xserver-vpsのビジネスプラン(HIGH帯)はA8.net通知(2026-08-29受信)により2026年8月31日〜
  9月中旬頃まで新規受付停止中のため一時非掲載**（`monthly_price_high`等を空欄化、
  `detail_review`からも言及を削除済み）。復元用の元の値は該当行の`notes`列に記載してある。
  再開時期が来たら公式サイトで受付再開を確認し、掲載を復元すること。

## その他

- `git init` 済み・ローカルにコミット履歴あり（ブランチ名は`main`。GitHubへのpushは
  まだ未実施 —— 詳細は上記「デプロイの自動化」参照）。`.gitignore` で `.env` /
  `config/service_account.json` / `data/services.json` / `public/` / `.venv/` を除外済み。
  新しい秘密情報（APIキー等）を追加する際は必ず`.gitignore`に追加してからコミットすること。
- ASP登録状況: A8.net・ValueCommerce登録済み（ValueCommerceは2026-08-27にサイト審査通過）。
  AccessTradeは審査結果待ち。ValueCommerceは「サイト単位の審査」と「広告主（企業）ごとの
  プログラム提携」が別なので、サイト審査通過だけでは個別企業のリンクはまだ発行されない
  ——A8.netと同じく、管理画面でプログラムを検索し企業ごとに提携申請する運用になる。
  `src/asp_clients/valuecommerce_client.py`は実装済み（商品API、`VALUECOMMERCE_TOKEN`が必要。
  管理画面「ツール」>「Webサービス」で発行）だが、これは商品情報取得用のオプション機構であり、
  基本のワークフローは他ASPと同じく人がリンクを取得してClaude Codeに共有する形で問題ない。
