"""Googleスプレッドシートの読み書きラッパー。

サービスアカウントのJSON鍵を使い、gspreadでシートに接続する。
シートの1行目はヘッダー（config/columns.yaml の key と一致させる）。
"""

from __future__ import annotations

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


class SheetsClient:
    def __init__(self, service_account_json: str, sheet_id: str, worksheet_name: str):
        creds = Credentials.from_service_account_file(service_account_json, scopes=SCOPES)
        self._gc = gspread.authorize(creds)
        self._ws = self._gc.open_by_key(sheet_id).worksheet(worksheet_name)

    def read_all_rows(self) -> list[dict]:
        """ヘッダー行をキーにした辞書のリストとして全行を返す。"""
        return self._ws.get_all_records()

    def update_row(self, row_index_1based: int, values_by_key: dict, header: list[str]) -> None:
        """1行分をキー→値の辞書で部分更新する（headerの列順に合わせて反映）。"""
        row = self._ws.row_values(row_index_1based)
        # ヘッダーより短い行はGoogle側で切り詰められているので長さを揃える
        row += [""] * (len(header) - len(row))

        for key, value in values_by_key.items():
            if key not in header:
                continue
            col_index = header.index(key)
            row[col_index] = value

        # gspread 6.1+ は values が第1引数（named argumentで明示して互換性の混乱を避ける）
        self._ws.update(values=[row], range_name=f"A{row_index_1based}")

    def header(self) -> list[str]:
        return self._ws.row_values(1)
