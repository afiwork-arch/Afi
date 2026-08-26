"""スプレッドシート（無ければローカルJSON）と各ASPを同期するオーケストレーター。

やること:
  1. 比較データ（料金・機能は手動入力済み）を読み込む
     - Google Sheets が設定されていればそこから
     - 未設定ならローカルの data/services.json をお試しデータとして使う
  2. 各行の asp_name / asp_program_id を見て、対応するASPクライアントで
     affiliate_link / asp_price_snapshot を埋める（対応していないASPはスキップしログ出力）
  3. 結果をスプレッドシートに書き戻し、data/services.json にもエクスポートする
     （後続の比較ページ生成スクリプトはこのJSONを読む想定）

料金・機能（monthly_price, disk_capacity など）はこのスクリプトでは一切変更しない。
それらは人が公式サイトを見て手動更新する運用のため。

使い方:
  python -m src.sync                 # 同期してシート+JSONを更新
  python -m src.sync --dry-run       # 取得結果を表示するだけで書き込みしない
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from src.asp_clients import A8NetClient, AccessTradeClient, ASPClient, ValueCommerceClient
from src.sheets_client import SheetsClient

ROOT = Path(__file__).resolve().parent.parent
LOCAL_JSON_PATH = ROOT / "data" / "services.json"
SAMPLE_JSON_PATH = ROOT / "data" / "services.sample.json"


def build_asp_clients() -> dict[str, ASPClient]:
    """.envの設定に応じて使えるASPクライアントだけを組み立てる。"""
    clients: dict[str, ASPClient] = {}

    vc_token = os.getenv("VALUECOMMERCE_TOKEN")
    if vc_token:
        clients["バリューコマース"] = ValueCommerceClient(token=vc_token)

    a8_dir = os.getenv("A8NET_REPORT_CSV_DIR")
    if a8_dir:
        clients["A8.net"] = A8NetClient(report_csv_dir=a8_dir)

    at_token = os.getenv("ACCESSTRADE_API_TOKEN")
    if at_token:
        base_url = os.getenv("ACCESSTRADE_API_BASE_URL") or None
        kwargs = {"api_token": at_token}
        if base_url:
            kwargs["base_url"] = base_url
        clients["AccessTrade"] = AccessTradeClient(**kwargs)

    return clients


def load_rows() -> tuple[list[dict], SheetsClient | None]:
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if sheet_id and sa_json and Path(sa_json).exists():
        sheets = SheetsClient(
            service_account_json=sa_json,
            sheet_id=sheet_id,
            worksheet_name=os.getenv("GOOGLE_SHEET_WORKSHEET_NAME", "services"),
        )
        return sheets.read_all_rows(), sheets

    print("[info] Google Sheets 未設定のため data/services.json（無ければsample）をローカルで使用します")
    path = LOCAL_JSON_PATH if LOCAL_JSON_PATH.exists() else SAMPLE_JSON_PATH
    with path.open(encoding="utf-8") as f:
        return json.load(f), None


def sync(dry_run: bool = False) -> list[dict]:
    load_dotenv()
    clients = build_asp_clients()
    rows, sheets = load_rows()
    header = sheets.header() if sheets else list(rows[0].keys()) if rows else []

    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    for i, row in enumerate(rows):
        asp_name = row.get("asp_name")
        program_id = row.get("asp_program_id")
        service_name = row.get("service_name", f"row{i}")

        if not asp_name or not program_id:
            continue

        client = clients.get(asp_name)
        if not client:
            print(f"[skip] {service_name}: 「{asp_name}」用のクライアントが未設定/未実装です")
            continue

        try:
            data = client.fetch_program(program_id)
        except NotImplementedError as e:
            print(f"[skip] {service_name}: {e}")
            continue
        except Exception as e:  # ASP側APIエラーなどで全体を止めない
            print(f"[warn] {service_name}: 取得に失敗しました ({e})")
            continue

        if data is None:
            print(f"[warn] {service_name}: 「{program_id}」のデータが見つかりませんでした")
            continue

        row["affiliate_link"] = data.affiliate_link or row.get("affiliate_link", "")
        row["asp_price_snapshot"] = data.price_snapshot or row.get("asp_price_snapshot", "")
        row["last_synced_at"] = now

        print(f"[ok] {service_name}: affiliate_link を更新しました")

        if sheets and not dry_run:
            sheets.update_row(
                row_index_1based=i + 2,  # 1行目はヘッダー
                values_by_key=row,
                header=header,
            )

    if not dry_run:
        LOCAL_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOCAL_JSON_PATH.open("w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"[ok] {LOCAL_JSON_PATH} を書き出しました")

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="書き込みせず取得結果だけ表示する")
    args = parser.parse_args()
    sync(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
