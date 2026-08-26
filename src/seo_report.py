"""Google Search Console + Cloudflare Web Analytics のデータをレポート化する。

  python -m src.seo_report

直近28日間の「検索クエリ(Search Console)」「ページ別アクセス数(Cloudflare Web
Analytics)」を取得し、SEO_REPORT.md に出力する。自動での記事作成・判断はしない
（あくまで「次に何を書くか」を検討するための材料を一覧化するだけ）。

必要な環境変数:
  GOOGLE_SERVICE_ACCOUNT_JSON  既存のスプレッドシート用サービスアカウント鍵。
                               Search Console側でこのアカウントに閲覧権限を付与済みであること。
  CLOUDFLARE_ANALYTICS_TOKEN   Account Analytics: Read 権限を持つCloudflare APIトークン。
  CLOUDFLARE_ACCOUNT_ID        Cloudflareのアカウントid。
"""

from __future__ import annotations

import os
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "SEO_REPORT.md"
SITE_URL = "https://sabanavi-hikaku.com/"


def fetch_search_console_rows(dimension: str, start: str, end: str, row_limit: int = 20) -> list[dict]:
    creds = Credentials.from_service_account_file(
        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"],
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
    )
    session = AuthorizedSession(creds)
    encoded = urllib.parse.quote(SITE_URL, safe="")
    resp = session.post(
        f"https://www.googleapis.com/webmasters/v3/sites/{encoded}/searchAnalytics/query",
        json={"startDate": start, "endDate": end, "dimensions": [dimension], "rowLimit": row_limit},
    )
    resp.raise_for_status()
    return resp.json().get("rows", [])


def fetch_cloudflare_pageviews(start: str, end: str, limit: int = 20) -> list[dict]:
    token = os.environ["CLOUDFLARE_ANALYTICS_TOKEN"]
    account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    query = """
    query ($accountTag: String!, $start: Time!, $end: Time!, $limit: Int!) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          rumPageloadEventsAdaptiveGroups(
            limit: $limit
            orderBy: [count_DESC]
            filter: {datetime_geq: $start, datetime_leq: $end}
          ) {
            count
            dimensions {
              requestPath
            }
          }
        }
      }
    }
    """
    resp = requests.post(
        "https://api.cloudflare.com/client/v4/graphql",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": query,
            "variables": {"accountTag": account_id, "start": start, "end": end, "limit": limit},
        },
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise RuntimeError(f"Cloudflare GraphQL API error: {data['errors']}")
    accounts = data["data"]["viewer"]["accounts"]
    return accounts[0]["rumPageloadEventsAdaptiveGroups"] if accounts else []


def build() -> None:
    load_dotenv(dotenv_path=ROOT / ".env")

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=28)
    start_str, end_str = start_date.isoformat(), end_date.isoformat()

    query_rows = fetch_search_console_rows("query", start_str, end_str, row_limit=20)
    page_rows = fetch_search_console_rows("page", start_str, end_str, row_limit=20)

    cf_start = f"{start_str}T00:00:00Z"
    cf_end = f"{end_str}T23:59:59Z"
    pageviews = fetch_cloudflare_pageviews(cf_start, cf_end, limit=20)

    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# SEOレポート",
        "",
        f"生成日時: {generated_at}(集計期間: {start_str} 〜 {end_str}、直近28日間)",
        "",
        "`python -m src.seo_report` を再実行すればいつでも最新化できます。自動判断はしないので、",
        "この内容を見ながら次に書く記事・追加する企業を検討してください。",
        "",
        "## 検索クエリ(Google Search Console)",
        "",
    ]

    if query_rows:
        lines += ["| クエリ | クリック数 | 表示回数 | 平均掲載順位 |", "|---|---|---|---|"]
        for row in query_rows:
            q = row["keys"][0]
            lines.append(
                f"| {q} | {row['clicks']} | {row['impressions']} | {row['position']:.1f} |"
            )
    else:
        lines.append("(まだデータがありません。登録直後はデータが溜まるまで数日〜1週間かかります)")

    lines += ["", "## 検索流入があったページ(Google Search Console)", ""]
    if page_rows:
        lines += ["| ページ | クリック数 | 表示回数 | 平均掲載順位 |", "|---|---|---|---|"]
        for row in page_rows:
            p = row["keys"][0]
            lines.append(
                f"| {p} | {row['clicks']} | {row['impressions']} | {row['position']:.1f} |"
            )
    else:
        lines.append("(まだデータがありません)")

    lines += ["", "## ページ別アクセス数(Cloudflare Web Analytics)", ""]
    if pageviews:
        lines += ["| パス | ページビュー数 |", "|---|---|"]
        for row in pageviews:
            lines.append(f"| {row['dimensions']['requestPath']} | {row['count']} |")
    else:
        lines.append("(まだデータがありません)")

    lines.append("")
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] SEOレポートを {OUTPUT_PATH} に出力しました")


if __name__ == "__main__":
    build()
