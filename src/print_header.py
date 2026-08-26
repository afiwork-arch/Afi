"""config/columns.yaml からスプレッドシートの1行目（ヘッダー）を作るための補助スクリプト。

初回セットアップ時に:
  python -m src.print_header
を実行し、出力された key 行をGoogleスプレッドシートの1行目にそのまま貼り付ける。
"""

from __future__ import annotations

from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "columns.yaml"


def main() -> None:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    columns = config["columns"]
    keys = [c["key"] for c in columns]
    labels = [c["label"] for c in columns]

    print(f"ジャンル: {config['genre']}\n")
    print("▼ スプレッドシート1行目に貼る（key。スクリプトが読み書きする列名）")
    print("\t".join(keys))
    print("\n▼ 参考: 人間向けラベル（2行目や別シートのメモ用）")
    print("\t".join(labels))


if __name__ == "__main__":
    main()
