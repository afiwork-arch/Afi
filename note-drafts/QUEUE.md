# note投稿キュー（サバナビ送客用）

毎月 **1日・15日** に、下書き生成ルーティン（cloud routine
`trig_01Psfchb5krahtGb3VGcvXaM`）がこのキューの先頭（未着手）の題材を1本
下書き化し、`note-drafts/YYYY-MM-DD_slug.md` として出力する。
ユーザーが内容を確認し、問題なければ手動でnoteに投稿し、この表の状態を更新する。

**事実ソースは `content/articles/*.md`（＝すでにファクトチェック済みの記事本文）のみ。**
`data/services.json` は `.gitignore` 済みでクラウドのチェックアウトには存在しないため、
ルーティンはこれに依存しない。記事本文に無い数字は書かず「(最新の金額は公式サイトで
ご確認ください)」とぼかす。

## 運用フロー

1. ルーティンが `status: 未着手` の一番上の題材を選ぶ（SEO_REPORT.md に関連クエリが
   出ていれば、それを優先的に拾って題材を差し込んでよい）
2. `data/services.json` の既存データ＋既存記事（`content/articles/`）だけで書ける範囲で
   下書きを作成（新規のファクトチェックが要る内容は避ける）。
   - 冒頭にPR表記：`※本記事にはプロモーション（アフィリエイト広告）を含みます。…`
   - 末尾に「投稿前メモ」HTMLコメント（タイトル案／ハッシュタグ／注意点）
   - サバナビへのリンクは `?utm_source=note&utm_medium=referral&utm_campaign=<slug>` を付与
   - noteは表が崩れるので比較は箇条書きで書く
3. 生成した下書きファイルをコミット（GitHub Actions自身にpushさせる方式）。
   この表の該当行を `status: 下書き済み` に更新し、`draft` にファイル名を記入
4. ユーザーがレビュー → noteに投稿 → `status: 投稿済み`、`posted` に投稿日とnote URLを記入
5. 投稿済みが増えたら、このファイル末尾の「ネタの追加候補」から新しい行を上に補充する

## ハッシュタグ（基本セット）

`#レンタルサーバー #ブログ運営 #WordPress #ブログ初心者 #サイト運営`

- 構成の考え方：exact-intent（#レンタルサーバー）1つ＋読者層（#ブログ運営／#ブログ初心者／
  #サイト運営）3つ＋関連技術（#WordPress）1つ。3〜5個に収める
- 題材次第で1つ差し替え：料金系なら `#節約` `#副業`、始め方系なら `#ホームページ作成`
  `#副業ブログ`、VPN回なら `#セキュリティ` `#リモートワーク`
- 新規アカウントではハッシュタグ単体の集客力は小さい。効果の主役はコンテンツ＋X等での外部シェア

## キュー

| # | 題材 | slug | 元ネタ（content/articles/） | status | draft | posted |
|---|------|------|--------|--------|-------|--------|
| 1 | 主要7社の「更新後の料金」を調べて表にした | renewal-price | renewal-price.md | 下書き済み | 2026-08_renewal-price-announce.md | 未 |
| 2 | 「月額◯円〜」で選ぶと後で困る話（選び方3ポイント） | choosing | how-to-choose.md / hidden-costs.md | 下書き済み | 2026-08_rental-server-choosing.md | 未 |
| 3 | 自動バックアップ「無料標準」か「有料オプション」か 各社の違い | backup-diff | how-to-choose.md / lolipop-vs-sakura.md | 未着手 | | |
| 4 | レンタルサーバーの「初期費用」は本当に無料？各社の実態 | setup-fee | hidden-costs.md | 未着手 | | |
| 5 | 3年契約 vs 1年契約、どっちが得？更新後料金で考える | contract-term | renewal-price.md / hidden-costs.md | 未着手 | | |
| 6 | 独自ドメイン「永久無料」特典の落とし穴 | domain-perk | hidden-costs.md | 未着手 | | |
| 7 | ブログを始めるのにディスク容量は何GB必要？ | disk-capacity | how-to-choose.md | 未着手 | | |
| 8 | 無料お試し・返金保証があるサーバーの賢い使い方 | free-trial | free-trial.md | 未着手 | | |
| 9 | 老舗 vs 新興、レンタルサーバーはどっちが安心？ | veteran-vs-new | xserver-vs-conoha-wing.md / lolipop-vs-sakura.md | 未着手 | | |
| 10 | 表示速度で選ぶなら？速いと言われるサーバーの見分け方 | site-speed | site-speed.md | 未着手 | | |
| 11 | WordPressを最短で公開するまでの手順（一般向け） | wp-start | how-to-start-wordpress.md | 未着手 | | |
| 12 | サーバー移行は大変？乗り換えの手順と注意点 | migration | server-migration.md | 未着手 | | |

## ネタの追加候補（キューが減ったら上へ移す）

- VPNって必要？レンタルサーバーとの違い（vpnジャンル、軽め）
- 個人ブログの費用、1年でいくらかかる？（サーバー＋ドメインの実額シミュレーション）
- 2社の直接比較のnote版（例: エックスサーバー vs ロリポップ）
- SEO_REPORT.md で実際に流入しているクエリがあれば、それに寄せた解説記事
