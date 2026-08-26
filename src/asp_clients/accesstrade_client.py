"""AccessTrade 用クライアント（雛形・要確認あり）。

AccessTradeには「Advertiser Search API」（提携広告主一覧取得）や
「Link Locator API」（提携リンク自動生成）が存在することは公開情報から
確認できたが、正確なエンドポイントURLと認証ヘッダー名は
パートナー管理画面ログイン後のAPIリファレンスでのみ確認できる
（未ログインの一般公開ページには記載がなかった）。

そのため、このファイルの ENDPOINT / 認証ヘッダー名は「よくある形」を
仮置きしたものであり、実装前に必ず以下で実際の値に差し替えること:

  管理画面ログイン後 > ツール（または「Webサービス」）メニュー
  > APIリファレンス
"""

from __future__ import annotations

import requests

from .base import ASPClient, ASPProgramData

# TODO: 実際のベースURLに差し替える（管理画面のAPIリファレンスを参照）
DEFAULT_BASE_URL = "https://api.accesstrade.net"


class AccessTradeClient(ASPClient):
    name = "AccessTrade"

    def __init__(self, api_token: str, base_url: str = DEFAULT_BASE_URL, timeout: float = 10.0):
        if not api_token:
            raise ValueError("ACCESSTRADE_API_TOKEN が未設定です")
        self._token = api_token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def fetch_program(self, program_id: str) -> ASPProgramData | None:
        # TODO: Advertiser Search API の実際のパス/パラメータ名に差し替える
        raise NotImplementedError(
            "AccessTradeの実エンドポイントが未確認のため未実装。"
            "管理画面のAPIリファレンスを確認してから実装すること。"
        )

    def _request(self, method: str, path: str, **kwargs) -> dict:
        # TODO: 実際の認証方式（Bearerトークンか、クエリパラメータか）を確認して調整する
        headers = {"Authorization": f"Bearer {self._token}"}
        resp = requests.request(
            method, f"{self._base_url}{path}", headers=headers, timeout=self._timeout, **kwargs
        )
        resp.raise_for_status()
        return resp.json()
