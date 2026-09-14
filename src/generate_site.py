"""スプレッドシート同期済みの data/services.json と content/articles/*.md から
静的サイト（public/ フォルダ）を生成する。

  python -m src.generate_site

出力された public/ フォルダをそのまま Cloudflare Pages / GitHub Pages 等の
静的ホスティングにデプロイする想定（サーバー側の処理は一切不要）。
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

import frontmatter
import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
CONTENT_DIR = ROOT / "content" / "articles"
PAGES_DIR = ROOT / "content" / "pages"
DATA_PATH = ROOT / "data" / "services.json"
COLUMNS_PATH = ROOT / "config" / "columns.yaml"
OUTPUT_DIR = ROOT / "public"

SITE_TITLE = "サバナビ"  # サイトのブランド名
SITE_BASE_URL = "https://sabanavi-hikaku.com"  # 独自ドメイン（末尾スラッシュなし）

# 記事本文(content/articles/*.md)内で {{alias:slug}} / {{alias:slug:mid}} / {{alias:slug:high}}
# と書くと、data/services.json の該当行から値を差し込む。手打ちの数字はスプレッドシートの
# 更新時にズレる(ミス・更新漏れ)ため、料金・スペックなど「シートの値そのもの」を記事に書きたい
# 箇所は必ずこの記法を使うこと。存在しないslug/フィールドを参照した場合はビルドを失敗させる
# (サイレントに空欄・古い値のままにしない)。詳細はCLAUDE.md参照。
PLACEHOLDER_RE = re.compile(r"\{\{(\w+):([a-z0-9_-]+)(?::(mid|high))?\}\}")
PLACEHOLDER_ALIASES = {
    "price": "monthly_price",
    "setup_fee": "setup_fee",
    "disk": "disk_capacity",
    "cpu_memory": "cpu_memory",
    "plan_name": "plan_name",
    "company": "company",
    "service_name": "service_name",
    "storage_type": "storage_type",
    "backup": "backup",
    "free_ssl": "free_ssl",
    "transfer_capacity": "transfer_capacity",
    "server_type": "server_type",
    "official_url": "official_url",
}
_YEN_FIELDS = {"monthly_price", "setup_fee"}


def resolve_placeholders(text: str, rows_by_slug: dict, source: str) -> str:
    def replace(m: re.Match) -> str:
        alias, slug, tier = m.group(1), m.group(2), m.group(3)
        base_field = PLACEHOLDER_ALIASES.get(alias)
        if base_field is None:
            raise ValueError(
                f"{source}: 未知の変数種別 '{alias}' です({m.group(0)})。"
                f"使えるのは {', '.join(sorted(PLACEHOLDER_ALIASES))} のいずれか。"
            )
        field = f"{base_field}_{tier}" if tier else base_field
        row = rows_by_slug.get(slug)
        if row is None:
            raise ValueError(f"{source}: slug '{slug}' が見つかりません({m.group(0)})。")
        value = row.get(field)
        if value is None or value == "":
            raise ValueError(
                f"{source}: '{slug}' の '{field}' が空です({m.group(0)})。"
                "このプラン帯が存在しない会社の可能性があるので、記事側の参照を見直してください。"
            )
        if base_field in _YEN_FIELDS and isinstance(value, (int, float)):
            return f"{int(value):,}"
        return str(value)

    return PLACEHOLDER_RE.sub(replace, text)


def load_columns() -> dict:
    with COLUMNS_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_rows() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    import json

    with DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_articles(default_genre: str, rows_by_slug: dict) -> list[dict]:
    articles = []
    if not CONTENT_DIR.exists():
        return articles

    for md_path in sorted(CONTENT_DIR.glob("*.md")):
        post = frontmatter.load(md_path)
        content = resolve_placeholders(post.content, rows_by_slug, source=md_path.name)
        html_content = markdown.markdown(content, extensions=["extra"])
        articles.append(
            {
                "title": post.get("title", md_path.stem),
                "slug": post.get("slug", md_path.stem),
                "date": str(post.get("date", "")),
                "genre": post.get("genre", default_genre),
                "html_content": html_content,
            }
        )

    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


def disk_capacity_gb(value) -> float:
    """比較表のソート用に「容量」を数値化する。「無制限」は最大値扱い、読み取れない場合は-1。"""
    if not value:
        return -1
    text = str(value)
    if "無制限" in text:
        return 10**6
    m = re.search(r"(\d+(?:\.\d+)?)\s*TB", text, re.IGNORECASE)
    if m:
        return float(m.group(1)) * 1024
    m = re.search(r"(\d+(?:\.\d+)?)\s*GB", text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return -1


def load_pages() -> list[dict]:
    pages = []
    if not PAGES_DIR.exists():
        return pages

    for md_path in sorted(PAGES_DIR.glob("*.md")):
        post = frontmatter.load(md_path)
        html_content = markdown.markdown(post.content, extensions=["extra"])
        pages.append(
            {
                "title": post.get("title", md_path.stem),
                "slug": post.get("slug", md_path.stem),
                "html_content": html_content,
            }
        )

    return pages


def build() -> None:
    config = load_columns()
    genres = config["genres"]
    default_genre = genres[0]["key"]

    rows = load_rows()
    rows_by_slug = {row["slug"]: row for row in rows if row.get("slug")}
    articles = load_articles(default_genre, rows_by_slug)
    pages = load_pages()
    public_columns = [c for c in config["columns"] if c.get("public")]

    for row in rows:
        row["genre"] = row.get("genre") or default_genre
        for tier_suffix in ("", "_mid", "_high"):
            price = row.get(f"monthly_price{tier_suffix}")
            row[f"_price_sort{tier_suffix}"] = (
                price if isinstance(price, (int, float)) and price != "" else 999999999
            )
            row[f"_disk_sort{tier_suffix}"] = disk_capacity_gb(row.get(f"disk_capacity{tier_suffix}"))

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    (OUTPUT_DIR / "articles").mkdir()
    (OUTPUT_DIR / "reviews").mkdir()
    for g in genres:
        if g["path"]:
            (OUTPUT_DIR / g["path"]).mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")

    # style.css / site.js / favicon類はそのままコピー
    shutil.copy(TEMPLATES_DIR / "style.css", OUTPUT_DIR / "style.css")
    shutil.copy(TEMPLATES_DIR / "site.js", OUTPUT_DIR / "site.js")
    for asset in (
        "favicon.svg",
        "favicon.ico",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "apple-touch-icon.png",
    ):
        shutil.copy(TEMPLATES_DIR / asset, OUTPUT_DIR / asset)

    # 比較表ページ（ジャンルごとに1ページ。例: server→public/index.html, vpn→public/vpn/index.html）
    index_tpl = env.get_template("index.html")
    for g in genres:
        genre_rows = [r for r in rows if r["genre"] == g["key"]]
        root = "../" if g["path"] else ""
        (OUTPUT_DIR / g["path"] / "index.html").write_text(
            index_tpl.render(
                site_title=SITE_TITLE,
                site_url=SITE_BASE_URL,
                genres=genres,
                genre=g["label"],
                genre_key=g["key"],
                public_columns=public_columns,
                rows=genre_rows,
                generated_at=generated_at,
                root=root,
                canonical_url=f"{SITE_BASE_URL}/{g['path']}",
            ),
            encoding="utf-8",
        )

    # 記事一覧ページ
    article_index_tpl = env.get_template("article_index.html")
    (OUTPUT_DIR / "articles" / "index.html").write_text(
        article_index_tpl.render(
            site_title=SITE_TITLE,
            site_url=SITE_BASE_URL,
            genres=genres,
            articles=articles,
            root="../",
            canonical_url=f"{SITE_BASE_URL}/articles/",
        ),
        encoding="utf-8",
    )

    # 記事詳細ページ
    article_tpl = env.get_template("article.html")
    for article in articles:
        (OUTPUT_DIR / "articles" / f"{article['slug']}.html").write_text(
            article_tpl.render(
                site_title=SITE_TITLE,
                site_url=SITE_BASE_URL,
                genres=genres,
                article=article,
                root="../",
                canonical_url=f"{SITE_BASE_URL}/articles/{article['slug']}",
            ),
            encoding="utf-8",
        )

    # 各社の個別レビューページ
    review_tpl = env.get_template("review.html")
    for row in rows:
        slug = row.get("slug")
        if not slug:
            continue
        (OUTPUT_DIR / "reviews" / f"{slug}.html").write_text(
            review_tpl.render(
                site_title=SITE_TITLE,
                site_url=SITE_BASE_URL,
                genres=genres,
                row=row,
                root="../",
                canonical_url=f"{SITE_BASE_URL}/reviews/{slug}",
            ),
            encoding="utf-8",
        )

    # 固定ページ（運営者情報・プライバシーポリシー・免責事項・お問い合わせ等）
    page_tpl = env.get_template("page.html")
    for page in pages:
        (OUTPUT_DIR / f"{page['slug']}.html").write_text(
            page_tpl.render(
                site_title=SITE_TITLE,
                site_url=SITE_BASE_URL,
                genres=genres,
                page=page,
                root="",
                canonical_url=f"{SITE_BASE_URL}/{page['slug']}",
            ),
            encoding="utf-8",
        )

    # sitemap.xml / robots.txt
    build_date = datetime.now().astimezone().strftime("%Y-%m-%d")
    paths = ["", "articles/"]
    paths += [g["path"] for g in genres if g["path"]]
    paths += [f"articles/{a['slug']}" for a in articles]
    paths += [f"reviews/{r['slug']}" for r in rows if r.get("slug")]
    paths += [f"{p['slug']}" for p in pages]

    sitemap_entries = "\n".join(
        f"  <url><loc>{SITE_BASE_URL}/{p}</loc><lastmod>{build_date}</lastmod></url>"
        for p in paths
    )
    sitemap_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{sitemap_entries}\n"
        "</urlset>\n"
    )
    (OUTPUT_DIR / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")

    robots_txt = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_BASE_URL}/sitemap.xml\n"
    (OUTPUT_DIR / "robots.txt").write_text(robots_txt, encoding="utf-8")

    print(
        f"[ok] {len(rows)}件の比較データ、{len(articles)}件の記事、"
        f"{len(pages)}件の固定ページ、sitemap.xml/robots.txt を public/ に出力しました"
    )


if __name__ == "__main__":
    build()
