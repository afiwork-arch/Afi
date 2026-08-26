"""A8.net 用クライアント（雛形）。

調査の結果、A8.netには「一般のメディア会員が自分の提携プログラム一覧や
成果レポートを取得できる公開APIは存在しない」ことを確認した。
公開されているのは以下の2つで、いずれも用途が異なる:

  - 成果データ連携API : 運用型広告（Google広告等）と連携するための機能
  - 確定API           : 広告主側が成果報酬の確定作業を自動化するための機能

そのため本雛形では、管理画面の「レポート」からCSVエクスポートした
ファイルを取り込む方式にしている。CSVの列名は実際にエクスポートした
ファイルを見て COLUMN_MAP を調整すること（本実装は仮の列名で書いている）。
"""

from __future__ import annotations

import csv
from pathlib import Path

from .base import ASPClient, ASPProgramData

# 実際にエクスポートしたCSVを見て、必要に応じてキー名を調整する。
COLUMN_MAP = {
    "program_id": "プログラムID",
    "program_name": "プログラム名",
    "affiliate_link": "提携リンク",
    "clicks": "クリック数",
    "conversions": "成果数",
    "reward": "確定報酬",
}


class A8NetClient(ASPClient):
    name = "A8.net"

    def __init__(self, report_csv_dir: str):
        self._dir = Path(report_csv_dir)
        self._cache: dict[str, dict] | None = None

    def fetch_program(self, program_id: str) -> ASPProgramData | None:
        rows = self._load()
        row = rows.get(program_id)
        if not row:
            return None
        return ASPProgramData(
            program_id=program_id,
            affiliate_link=row.get(COLUMN_MAP["affiliate_link"]),
            price_snapshot=None,  # A8.netのレポートには料金プラン情報は含まれない
            raw=row,
        )

    def _load(self) -> dict[str, dict]:
        if self._cache is not None:
            return self._cache

        rows: dict[str, dict] = {}
        if not self._dir.exists():
            self._cache = rows
            return rows

        for csv_path in self._dir.glob("*.csv"):
            for row in _read_csv_any_encoding(csv_path):
                program_id = row.get(COLUMN_MAP["program_id"])
                if program_id:
                    rows[program_id] = row

        self._cache = rows
        return rows


def _read_csv_any_encoding(path: Path) -> list[dict]:
    """A8.netのCSVエクスポートはShift_JIS(cp932)のことが多いため両対応にする。"""
    for encoding in ("cp932", "utf-8-sig"):
        try:
            with path.open(encoding=encoding, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{path} の文字コードを判定できませんでした（cp932/utf-8-sigで失敗）")
