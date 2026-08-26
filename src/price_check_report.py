"""毎月の価格チェック用リストを生成する。

  python -m src.price_check_report

data/services.json を読み込み、掲載中の会社ごとに「確認先URL」
「現在シートに記録している月額料金(LOW/MIDDLE/HIGH)」「アフィリエイトリンク」を
一覧化し、PRICE_CHECK.md に出力する。実際の価格変動の自動検知はしない
（このスクリプトは「毎月どこを見ればいいか」を一覧化するだけ）。

使い方:
  1. 月1回、python -m src.price_check_report を実行してPRICE_CHECK.mdを更新
  2. 表の「確認URL」を開き、記載中の価格と公式サイトの表示価格を見比べる
  3. ズレていればGoogleスプレッドシートを更新
  4. python -m src.generate_site でサイトを再ビルド・再デプロイ
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "services.json"
OUTPUT_PATH = ROOT / "PRICE_CHECK.md"


def fmt_price(value) -> str:
    if value is None or value == "":
        return "―"
    return f"{value}円"


def build() -> None:
    rows = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# 価格チェックリスト（月次確認用）",
        "",
        f"生成日時: {generated_at}",
        "",
        "毎月1回、各社の「確認URL」を開き、下表の記録価格と公式サイトの表示価格を見比べてください。",
        "ズレていたらGoogleスプレッドシートを更新し、`python -m src.generate_site` で",
        "サイトを再ビルド・再デプロイしてください。このファイル自体は",
        "`python -m src.price_check_report` を再実行すればいつでも最新化できます。",
        "",
        "| 会社 | 種別 | 確認URL | LOW | MIDDLE | HIGH | アフィリエイトリンク | 備考 |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in rows:
        name = row.get("service_name", "")
        stype = row.get("server_type", "") or "―"
        url = row.get("official_url") or "―"
        low = fmt_price(row.get("monthly_price"))
        mid = fmt_price(row.get("monthly_price_mid"))
        high = fmt_price(row.get("monthly_price_high"))
        aff = row.get("affiliate_link") or "**(未設定)**"
        notes = (row.get("notes") or "").replace("|", "/").replace("\n", " ")
        lines.append(f"| {name} | {stype} | {url} | {low} | {mid} | {high} | {aff} | {notes} |")

    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[ok] {len(rows)}社分のチェックリストを {OUTPUT_PATH} に出力しました")


if __name__ == "__main__":
    build()
