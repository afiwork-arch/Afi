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


def load_columns() -> dict:
    with COLUMNS_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_rows() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    import json

    with DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_articles() -> list[dict]:
    articles = []
    if not CONTENT_DIR.exists():
        return articles

    for md_path in sorted(CONTENT_DIR.glob("*.md")):
        post = frontmatter.load(md_path)
        html_content = markdown.markdown(post.content, extensions=["extra"])
        articles.append(
            {
                "title": post.get("title", md_path.stem),
                "slug": post.get("slug", md_path.stem),
                "date": str(post.get("date", "")),
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
    rows = load_rows()
    articles = load_articles()
    pages = load_pages()
    public_columns = [c for c in config["columns"] if c.get("public")]

    for row in rows:
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

    # 比較表ページ（トップ）
    index_tpl = env.get_template("index.html")
    (OUTPUT_DIR / "index.html").write_text(
        index_tpl.render(
            site_title=SITE_TITLE,
            site_url=SITE_BASE_URL,
            genre=config["genre"],
            public_columns=public_columns,
            rows=rows,
            generated_at=generated_at,
            root="",
        ),
        encoding="utf-8",
    )

    # 記事一覧ページ
    article_index_tpl = env.get_template("article_index.html")
    (OUTPUT_DIR / "articles" / "index.html").write_text(
        article_index_tpl.render(
            site_title=SITE_TITLE,
            site_url=SITE_BASE_URL,
            articles=articles,
            root="../",
        ),
        encoding="utf-8",
    )

    # 記事詳細ページ
    article_tpl = env.get_template("article.html")
    for article in articles:
        (OUTPUT_DIR / "articles" / f"{article['slug']}.html").write_text(
            article_tpl.render(
                site_title=SITE_TITLE, site_url=SITE_BASE_URL, article=article, root="../"
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
            review_tpl.render(site_title=SITE_TITLE, site_url=SITE_BASE_URL, row=row, root="../"),
            encoding="utf-8",
        )

    # 固定ページ（運営者情報・プライバシーポリシー・免責事項・お問い合わせ等）
    page_tpl = env.get_template("page.html")
    for page in pages:
        (OUTPUT_DIR / f"{page['slug']}.html").write_text(
            page_tpl.render(site_title=SITE_TITLE, site_url=SITE_BASE_URL, page=page, root=""),
            encoding="utf-8",
        )

    # sitemap.xml / robots.txt
    build_date = datetime.now().astimezone().strftime("%Y-%m-%d")
    paths = ["", "articles/"]
    paths += [f"articles/{a['slug']}.html" for a in articles]
    paths += [f"reviews/{r['slug']}.html" for r in rows if r.get("slug")]
    paths += [f"{p['slug']}.html" for p in pages]

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
