# 開発ツール比較アフィリエイトサイト — データ同期スクリプト雛形

ジャンル: レンタルサーバー（他ジャンルへの展開は [config/columns.yaml](config/columns.yaml) を参照）

## 前提として：ASP APIで分かったこと（重要）

A8.net／バリューコマース／AccessTradeの公開API仕様を調査した結果、
**「料金・機能プランを取得できる汎用APIはどのASPにも存在しない」**ことが分かりました。

| ASP | 公開されているAPI | 用途 | 料金プラン取得 |
|---|---|---|---|
| A8.net | 成果データ連携API／確定API | 運用型広告連携・広告主側の報酬確定自動化 | ✕（一般メディア会員向けAPIは無し。レポートはCSVエクスポートのみ） |
| バリューコマース | 商品API（Web Service API） | 「Webサービス対応プログラム」の商品検索・価格比較 | △（EC/物販系の対応広告主のみ。サーバー/SaaS/スクールは非対応が多い） |
| AccessTrade | Advertiser Search API／Link Locator API | 提携広告主一覧取得・リンク自動生成 | ✕ |

そのため、この雛形は **「料金・機能はスプレッドシートに人が手動更新する」を前提**にした設計にしています。
ASP側の役割は「アフィリエイトリンクの取得」「（バリューコマースのみ）対応広告主の価格スナップショット取得」に限定しています。

## 構成

```
config/columns.yaml       比較項目（列）の定義。ジャンルごとに複製して使う
data/services.sample.json ローカルお試し用のサンプルデータ
src/asp_clients/          ASPごとのクライアント
  base.py                 共通インターフェース
  valuecommerce_client.py 商品API実装（動作する想定。要トークン）
  a8net_client.py         CSVレポート取り込み方式（要: 実際のCSV列名への調整）
  accesstrade_client.py   雛形のみ。実エンドポイント/認証はログイン後リファレンスで要確認
src/sheets_client.py      Googleスプレッドシート読み書き（gspread）
src/sync.py               同期のメイン処理
src/print_header.py       columns.yaml からシートのヘッダー行を出力
src/generate_site.py      data/services.json + content/articles/*.md から静的サイトを生成
templates/                サイトのHTMLテンプレート（Jinja2）とCSS
content/articles/         記事の原稿（Markdown。ASP審査対策の記事もここに追加する）
public/                   生成された静的サイト（このフォルダをそのままデプロイする）
```

## セットアップ

Python 3.10以上が必要です（このマシンには実行可能なPythonが見つからなかったため、
コードは静的レビューのみで検証しています。実行前に `python --version` で確認してください）。

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
copy .env.example .env
```

`.env` に設定するもの:

- **Google Sheets**: Google Cloud Consoleでサービスアカウントを作成し鍵JSONをダウンロード、
  対象スプレッドシートをそのサービスアカウントのメールアドレスに「編集者」で共有する。
  未設定でも `data/services.sample.json` を使ってローカルで動作確認できます。
- **バリューコマース**: 管理画面でWebサービス用トークンを発行して設定。
- **A8.net**: 管理画面の「レポート」からCSVをエクスポートし、`A8NET_REPORT_CSV_DIR` のフォルダに置く。
- **AccessTrade**: 管理画面ログイン後のAPIリファレンスで実際のエンドポイント/認証方式を確認し、
  `src/asp_clients/accesstrade_client.py` のTODO部分を実装してから使う（現状は未実装エラーを返す）。

## 使い方

```bash
# 1. 初回: スプレッドシートの1行目に貼るヘッダーを出力
python -m src.print_header

# 2. 比較データ（monthly_price 等）を各社公式サイトを見ながら手動入力
#    asp_name / asp_program_id も忘れずに入れる

# 3. ASPからアフィリエイトリンク・価格スナップショットを取得して反映
python -m src.sync            # シート（未設定ならローカルJSON）を更新
python -m src.sync --dry-run  # 取得結果を表示するだけ
```

実行結果は `data/services.json` にも出力されます。

```bash
# 4. 比較ページ・記事ページを静的サイトとして生成
python -m src.generate_site
```

`public/` フォルダにサイト一式（HTML/CSS）が出力されます。サーバーサイドの処理は無いので、
`public/` の中身をそのまま Cloudflare Pages や GitHub Pages などの静的ホスティングにデプロイするだけで公開できます。

ローカルでの見た目確認:

```bash
cd public
python -m http.server 8000
# ブラウザで http://127.0.0.1:8000 を開く
```

### 記事コンテンツの追加

`content/articles/` に Markdown ファイルを追加すると `python -m src.generate_site` で自動的にページ化されます。

```markdown
---
title: 記事タイトル
date: 2026-08-26
slug: url-slug
---

本文をMarkdownで書く。
```

AccessTradeなどの審査では最低5〜10記事程度の投稿が目安とされているため、
`content/articles/how-to-choose.md` と `shared-vs-vps.md` を参考に、比較ジャンルに関する
記事をいくつか追加してから登録申請することを推奨します。

## 既知の制約・要確認事項

- `accesstrade_client.py` はエンドポイントURL・認証ヘッダー名が未確認のプレースホルダーです。
  管理画面ログイン後のAPIリファレンスを見て実装してください。
- `a8net_client.py` のCSV列名（`COLUMN_MAP`）は仮です。実際にエクスポートしたCSVの
  ヘッダーに合わせて調整してください。
- `valuecommerce_client.py` のレスポンスJSONのキー名（価格フィールド等）は広告主/カテゴリで
  揺れる可能性があります。実レスポンスで一度確認することを推奨します。
- 料金・機能列（monthly_price など）はこのスクリプトでは一切更新しません。人手更新が前提です。
