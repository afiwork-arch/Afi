"""ASPクライアントの共通インターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ASPProgramData:
    """ASPから取得できた1件分のデータ（比較行にマージされる）。"""

    program_id: str
    affiliate_link: str | None = None
    price_snapshot: str | None = None
    raw: dict | None = None


class ASPClient(ABC):
    """各ASP実装が満たすべき最小インターフェース。"""

    name: str

    @abstractmethod
    def fetch_program(self, program_id: str) -> ASPProgramData | None:
        """program_id（=スプレッドシートの asp_program_id 列）に対応するデータを1件取得する。

        見つからない場合や未対応の場合は None を返す。
        """
        raise NotImplementedError
