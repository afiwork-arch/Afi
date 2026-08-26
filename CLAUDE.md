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
  プロジェクト名 `sparkling-waterfall-3cf7`、独自ドメイン `sabanavi-hikaku.com`）に**手動**で
  デプロイする。CI/CDは未設定 —— コード変更後は毎回「`public/` の中身を再アップロードしてください」
  とユーザーに伝えること。

## ビルドコマンド

```bash
# リポジトリルートで実行（-m 指定が必須。venvはこのマシンでは c:/Users/gudej/Desktop/afi/.venv）
.venv/Scripts/python.exe -m src.generate_site
```

スプレッドシートの内容を `data/services.json` に反映してからビルドする（キャッシュなので
シートを直接編集しただけではサイトに反映されない）:

```bash
PYTHONPATH="c:/Users/gudej/Desktop/afi" .venv/Scripts/python.exe -c "
from dotenv import load_dotenv
load_dotenv(dotenv_path='c:/Users/gudej/Desktop/afi/.env')
import os, json
from src.sheets_client import SheetsClient
sc = SheetsClient(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'), os.getenv('GOOGLE_SHEET_ID'), os.getenv('GOOGLE_SHEET_WORKSHEET_NAME'))
rows = sc.read_all_rows()
json.dump(rows, open('data/services.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
"
```

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
   `sc._ws.append_row(values)` が定番パターン）。`slug`（英数字、reviews/配下のURLになる）と
   `diagnosis_label`（診断ツールのボタン文言、「〜重視」で統一）を忘れずに埋める。
4. `data/services.json` を再生成 → `python -m src.generate_site` → HTTPスモークテスト。
5. ユーザーに再デプロイを促す。

新しい列をヘッダーに追加する場合、Googleスプレッドシートのデフォルトグリッドは26列（A〜Z）まで
なので、超える場合は `sc._ws.update_cell()` の前に `sc._ws.add_cols(n)` で列数を拡張しないと
`APIError: [400] Range (...) exceeds grid limits` になる（列数追加系のスクリプトを書くときは
毎回チェックすること）。

## データ列（`config/columns.yaml`）

`type: manual/asp/system` と `public: true/false` を持つ。主要列: `service_name`, `slug`
（内部利用、非公開）, `recommend_comment`（一言）, `diagnosis_label`（診断ボタン文言）,
`detail_review`（3〜5文の詳細レビュー、各社レビュー用ドロップダウンとreviews/個別ページで使用）,
`company`, `monthly_price`, `setup_fee`, `disk_capacity`, `transfer_capacity`, `server_type`
（「共用」「VPS」など。診断STEP1やソートに使う軸なので値の表記揺れに注意）, `free_ssl`,
`official_url`, `asp_name`, `affiliate_link`, `notes`（未確認事項のメモ）。

比較表のLOW/MIDDLE/HIGHプラン切り替え用に `plan_name_mid` / `monthly_price_mid` /
`setup_fee_mid` / `disk_capacity_mid` と `_high` 版も存在する（詳細は下記「比較表のプラン帯
切り替え」参照）。中位・上位プランが無い会社は空欄でよい。

新しいジャンル（サーバー以外）に展開する場合は `columns.yaml` をコピーして `genre` を変える想定
（README参照）。

## フロントエンドの設計規約（このセッションで確立したもの）

- **ライトテーマ限定**。`prefers-color-scheme: dark` には対応しない方針（ユーザー指示）。
  `:root { color-scheme: light; }`。
- **日本語テキストに `ch` 単位を使わない**。全角文字の実測幅とズレて意図せず折り返す原因になった
  ため、`max-width` はpx指定に統一済み。短い「」引用フレーズは `.kw`（`white-space: nowrap`、
  480px以下では解除）で囲み、フレーズ途中の改行を防ぐ。
- **ボタン群は役割ごとに見た目を変える**。同じpage内に複数のボタングループが並ぶと同じ見た目では
  混同されるとフィードバックを受けた。現状の使い分け:
  - `.diag-btn`（診断ツール）: ピル型タグ選択chip、選択時チェックマーク＋ポップアニメーション
  - `.sort-btn`（比較表ソート）: グレートレイに浮かぶセグメントコントロール
  - `.table-more-btn`（比較表もっと見る）: 点線ボーダーの控えめな全幅ボタン
  新しいボタン群を追加するときは、既存のどれとも視覚的に紛れないデザインを検討すること。
  （過去に存在した`.pick-chip`＝ページ上部クイックピックの番号カードは、診断ツールと役割が
  重複し情報過多だったためユーザー指示で削除済み。復活させない）
- ホバー/press feedback（transform + box-shadow）と `@media (prefers-reduced-motion: reduce)`
  対応は全インタラクティブ要素で統一して入れている。新規追加時も踏襲する。
- 各社の詳細レビュー（`.reviews`セクション）は会社数が増えてきたため、アコーディオン方式から
  `<select id="review-select">` のドロップダウンで1社ずつ表示する方式に変更済み（`.review-panel`
  を`data-slug`で出し分け）。会社が増えても縦に伸びない設計。

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

## 診断ツール（`.diagnosis`, `templates/site.js`）

STEP1（サーバー種類=`server_type`）→ STEP2（予算感、`monthly_price` から自動バケット化・
スプレッドシートに列を増やさなくていい設計）→ STEP3（`diagnosis_label` で絞り込み）→ 結果、の
3問構成。候補が1社に絞れた時点で残りの質問はスキップする。パネル遷移は同一グリッドセルに
スタックした2枚を同時に逆方向へtranslateXさせるクロスフェード実装（`site.js` の `showPanel`）。
質問をさらに増やす場合はこのパターン（既存データ列から自動計算できる軸を優先）を踏襲すると
スプレッドシートの手入力を増やさずに済む。

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
- **今後の候補（未着手）**: Google Search Console連携（`google-site-verification`メタタグは
  設置済みなのでプロパティ登録は容易なはず。ただしユーザー自身のログイン操作が必要なため
  Claude Codeからは実行不可）、既存記事の加筆による情報量強化、被リンク獲得。

## コンプライアンス

- ステマ規制（景品表示法、2023年10月施行）対応で `base.html` にPR表示バー（`.pr-bar`）を常設。
- `content/pages/` に運営者情報・プライバシーポリシー・免責事項・お問い合わせを設置済み。
- 比較表脚注に「キャンペーン価格を含む場合がある」旨の打ち消し表示あり。新しい会社を追加する際も
  この表現と矛盾しない価格の選び方をする（上記「新しい会社を追加する手順」参照）。

## 既知の未確認事項

- mixhostの初期費用が未確認。
- xserver / conoha-wing / mixhost / lolipop / onamae / conoha-vps / colorfulbox の
  `transfer_capacity`（転送量）が未確認（`notes` 列に記載あり）。さくらのみ「無制限」を確認済み。

## その他

- このディレクトリは現時点で **gitリポジトリ化されていない**（`git status` はエラーになる）。
  バージョン管理が必要になったら `git init` から始める必要がある（ユーザーに確認してから）。
- ASP登録状況: A8.net登録済み。ValueCommerce／AccessTradeは審査結果待ち（承認され次第、
  同様のワークフローでリンクを追加する）。
