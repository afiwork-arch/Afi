"""バリューコマース 商品API（Web Service API）クライアント。

参考: https://pub-docs.valuecommerce.ne.jp/docs/as-63-item-api/
- GET http://webservice.valuecommerce.ne.jp/productdb/search
- 認証はクエリパラメータ token
- 「Webサービス対応プログラム」で提携している広告主の商品のみ取得できる。
  レンタルサーバー/SaaS/スクール系は対応していない広告主も多いため、
  事前に管理画面の「広告」>「対応機能別」>「Webサービス」で対象を確認すること。
- レスポンスのJSONキー名（price系フィールド名など）は広告主/カテゴリで揺れることがあるため、
  本実装では "price" を含むキーを緩く探す実装にしている。実運用前に実レスポンスで要確認。
"""

from __future__ import annotations

import requests

from .base import ASPClient, ASPProgramData

SEARCH_ENDPOINT = "http://webservice.valuecommerce.ne.jp/productdb/search"


class ValueCommerceClient(ASPClient):
    name = "バリューコマース"

    def __init__(self, token: str, timeout: float = 10.0):
        if not token:
            raise ValueError("VALUECOMMERCE_TOKEN が未設定です")
        self._token = token
        self._timeout = timeout

    def fetch_program(self, program_id: str) -> ASPProgramData | None:
        """program_id は ecCode（広告主サイトコード）として扱う。"""
        items = self.search_items(ec_code=program_id)
        if not items:
            return None

        item = items[0]
        return ASPProgramData(
            program_id=program_id,
            affiliate_link=item.get("link") or item.get("url"),
            price_snapshot=self._extract_price(item),
            raw=item,
        )

    def search_items(
        self,
        keyword: str | None = None,
        category: str | None = None,
        ec_code: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        params = {
            "token": self._token,
            "format": "json",
            "results": limit,
        }
        if keyword:
            params["keyword"] = keyword
        if category:
            params["category"] = category
        if ec_code:
            params["ecCode"] = ec_code

        resp = requests.get(SEARCH_ENDPOINT, params=params, timeout=self._timeout)
        resp.raise_for_status()
        data = resp.json()

        # レスポンス構造はRSS由来のためネストが深い場合がある。
        # 実際のキー名は初回実行時にログ/デバッグで確認して調整すること。
        items = data.get("items") or data.get("feed", {}).get("entry") or []
        return items if isinstance(items, list) else [items]

    @staticmethod
    def _extract_price(item: dict) -> str | None:
        for key, value in item.items():
            if "price" in key.lower():
                return str(value)
        return None
