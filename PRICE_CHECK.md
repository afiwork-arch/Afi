# 価格チェックリスト（月次確認用）

生成日時: 2026-08-26 22:15

毎月1回、各社の「確認URL」を開き、下表の記録価格と公式サイトの表示価格を見比べてください。
ズレていたらGoogleスプレッドシートを更新し、`python -m src.generate_site` で
サイトを再ビルド・再デプロイしてください。このファイル自体は
`python -m src.price_check_report` を再実行すればいつでも最新化できます。

| 会社 | 種別 | 確認URL | LOW | MIDDLE | HIGH | アフィリエイトリンク | 備考 |
|---|---|---|---|---|---|---|---|
| エックスサーバー | 共用 | https://www.xserver.ne.jp/ | 693円 | 1980円 | 3762円 | https://px.a8.net/svt/ejp?a8mat=4BAEXD+78RVQQ+CO4+61C2Q | スタンダードプラン。キャンペーン価格(通常990円、2026/9/7まで)。転送量は要確認 |
| ConoHa WING | 共用 | https://www.conoha.jp/ | 970円 | 1925円 | 3850円 | https://px.a8.net/svt/ejp?a8mat=4BAEXD+79DBCI+50+5SJACI | ベーシックプラン(メモリ8GB/vCPU6コア)。キャンペーン価格(通常33%OFF、2026/9/9 16:00まで)。転送量は要確認 |
| mixhost | 共用 | https://mixhost.jp/ | 880円 | 968円 | 1408円 | https://px.a8.net/svt/ejp?a8mat=4BAEXD+79YQYA+3JTE+5YJRM | スタンダードプラン・1年更新(税込968円)。初期費用は要確認(inode数20万、推奨20万PV/月) (バックアップは現行のスタンダードプラン以上で無料標準。より安いライトプランにはバックアップ無し) |
| ロリポップ | 共用 | https://lolipop.jp/ | 330円 | 660円 | ― | https://px.a8.net/svt/ejp?a8mat=4BAEXD+7AK6K2+348+5YZ76 | ライトプラン(月額330円〜、WordPress対応)。2023年5月より全プラン初期費用無料。転送量は要確認 |
| さくらのレンタルサーバ | 共用 | https://rs.sakura.ad.jp/ | 121円 | 500円 | 1980円 | https://px.a8.net/svt/ejp?a8mat=4BAEXD+786G4Y+D8Y+65U42 | 36ヶ月一括契約時の月額換算(ユーザー提供の公式スクショで確認)。LOW=ライト/MID=スタンダード/HIGH=ビジネスの3段階。マネージドサーバミディアム(1TB)は製品カテゴリが異なるため対象外。転送量は要確認 |
| お名前.com レンタルサーバー | 共用 | https://www.onamae.com/server/ | 2398円 | ― | ― | https://px.a8.net/svt/ejp?a8mat=4BAEXJ+2CJKOI+50+35CAFM | ベーシックプラン(唯一のプラン)。初月無料キャンペーン(2ヶ月目以降2,398円/月)。他社より月額はやや高めなので価格重視の方には不向き。転送量は要確認 |
| ConoHa VPS | VPS | https://vps.conoha.jp/ | 460円 | 763円 | 1380円 | https://px.a8.net/svt/ejp?a8mat=4BAEXJ+2EBVHU+50+4Z0M6A | 512MBプラン・1ヶ月契約時の料金(更新後も同額)。長期契約でさらに割引(36ヶ月なら293円/月)。VPSのため要サーバー管理知識。転送量は要確認 (バックアップの無料/有料は要確認) |
| カラフルボックス | 共用 | https://www.colorfulbox.jp/ | 528円 | 436円 | 733円 | https://px.a8.net/svt/ejp?a8mat=4BAEXJ+2DQFW2+42SG+62U36 | BOX1(最安)プラン、36ヶ月契約時の料金(初回割引なしの通常価格)。初期費用は3ヶ月以上契約で無料、1ヶ月契約のみ2,200円。目安PV数30,000/月。転送量は要確認 |
| お名前.com VPS (KVM) | VPS | https://www.onamae.com/server/ | 873円 | 1209円 | 3398円 | https://px.a8.net/svt/ejp?a8mat=4BAEXJ+2CJKOI+50+35LPXU | 1GBプラン・12ヶ月払い時の実質月額を基準に採用(12/24/36ヶ月とも同額のため下限価格として妥当)。MID=2GBプラン/HIGH=4GBプラン(初期費用5,951円、支払い期間に関わらず一律)。1ヶ月払いのみの単月価格(985/1446/4065円)は他社と算出基準が揃わないため不採用。official_urlはレンタルサーバー総合ページの暫定リンク(VPS専用ページURLは要確認)。転送量・無料SSLは要確認 (バックアップの無料/有料は要確認) |
