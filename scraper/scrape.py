"""
Scraper tin tức đất đai và pháp luật - snnmt.daklak.gov.vn
Sử dụng Playwright (async) để cào dữ liệu và lưu ra news.json.

Cách chạy:
    python scrape.py
"""
import asyncio
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dateutil import parser as date_parser
from playwright.async_api import async_playwright
from slugify import slugify

BASE_URL = "https://snnmt.daklak.gov.vn"
OUTPUT_PATH = Path(__file__).parent.parent / "frontend" / "public" / "news.json"

# ─────────────────────────────────────────────────────────────────────────────
# Bộ lọc từ khóa đất đai và pháp luật
# ─────────────────────────────────────────────────────────────────────────────
LAND_AND_LAW_KEYWORDS = [
    # Đất đai
    "đất", "đất đai", "thửa đất", "địa chính", "thu hồi đất", "giá đất",
    "bảng giá đất", "gcnqsdđ", "sổ đỏ", "sổ hồng", "quyền sử dụng đất",
    "chuyển mục đích sử dụng đất", "tái định cư", "bồi thường", "giải phóng mặt bằng",
    "văn phòng đăng ký đất đai", "đo đạc", "quy hoạch sử dụng đất", "kế hoạch sử dụng đất",
    "vbdlis", "đăng ký đất đai", "giao đất", "cho thuê đất", "lấn chiếm đất",
    "tranh chấp đất", "đấu giá đất", "cấp giấy chứng nhận",
    # Pháp luật
    "luật", "nghị định", "thông tư", "quyết định", "xử phạt", "vi phạm",
    "thanh tra", "kiểm tra", "khiếu nại", "tố cáo", "pháp luật", "tư pháp",
    "hành chính", "quy chuẩn", "tiêu chuẩn", "chỉ thị", "thủ tục hành chính",
    "tthc", "phổ biến giáo dục pháp luật", "pbgdpl", "văn bản quy phạm",
]

def is_land_or_law_related(title: str, summary: str = "", content: str = "") -> bool:
    """Kiểm tra bài viết có liên quan đến đất đai hoặc pháp luật không."""
    search_text = f"{title} {summary} {content}".lower()
    return any(kw in search_text for kw in LAND_AND_LAW_KEYWORDS)

# ─────────────────────────────────────────────────────────────────────────────
# Cấu hình các mục nguồn cào thực tế trên snnmt.daklak.gov.vn
# ─────────────────────────────────────────────────────────────────────────────
SECTIONS = [
    {
        "category": "tin-tuc",
        "list_url": f"{BASE_URL}/thong-bao.html",
        "max_pages": 3,
    },
    {
        "category": "tin-tuc",
        "list_url": f"{BASE_URL}/categories/cai-cach-hanh-chinh-65.html",
        "max_pages": 3,
    },
    {
        "category": "tin-tuc",
        "list_url": f"{BASE_URL}/categories/tin-tuc-su-kien-6.html",
        "max_pages": 4,
    },
    {
        "category": "tin-tuc",
        "list_url": f"{BASE_URL}/categories/thong-tin-chuyen-nganh-2.html",
        "max_pages": 3,
    },
]

ARTICLE_LINK_SELECTORS = [
    ".categoryList .article-item h4 a[href]",
    ".categoryList a[href*='.html']",
    ".documents-scroll-content a[href*='.html']",
    ".article-item h4 a",
    ".article-item a[href*='.html']",
    "h4 a[href*='.html']",
    "h3 a[href*='.html']",
    ".card a[href*='.html']",
]

CONTENT_SELECTORS = [
    ".article-content",
    "#PageDetail .full-text",
    ".full-text",
    "#PageDetail",
    "article .content",
    ".news-content",
]

VN_TZ = timezone(timedelta(hours=7))


def now_vn() -> str:
    return datetime.now(VN_TZ).isoformat()


def add_days(iso_str: str, days: int = 30) -> str:
    try:
        dt = date_parser.parse(iso_str)
        return (dt + timedelta(days=days)).isoformat()
    except Exception:
        return now_vn()


def parse_vn_date(text: str) -> str | None:
    """Parse ngày dạng tiếng Việt: '14/09/2026', 'Ngày 15/01/2025', v.v."""
    if not text:
        return None
    cleaned = re.sub(r"(ngày|cập nhật|đăng ngày|đăng lúc|lúc|cập nhật lúc:?):?\s*", "", text, flags=re.IGNORECASE).strip()
    match = re.search(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", cleaned)
    if match:
        day, month, year = match.groups()
        try:
            dt = datetime(int(year), int(month), int(day), tzinfo=VN_TZ)
            return dt.isoformat()
        except ValueError:
            pass
    try:
        return date_parser.parse(cleaned, dayfirst=True).replace(tzinfo=VN_TZ).isoformat()
    except Exception:
        return None


def make_slug(title: str) -> str:
    return slugify(title, allow_unicode=False, separator="-")


def fix_image_urls(html: str) -> str:
    """Chuyển tất cả src ảnh tương đối thành URL tuyệt đối."""
    def replace_src(m):
        src = m.group(1).strip()
        if not src or src.startswith("data:"):
            return m.group(0)
        if src.startswith("http://") or src.startswith("https://"):
            return m.group(0)
        if src.startswith("//"):
            return f'src="https:{src}"'
        if src.startswith("/"):
            return f'src="{BASE_URL}{src}"'
        return f'src="{BASE_URL}/{src}"'

    return re.sub(r'src="([^"]*)"', replace_src, html)


def extract_thumbnail(html: str, page_og_image: str = "") -> str:
    """Lấy thumbnail từ og:image hoặc ảnh hợp lệ đầu tiên trong HTML."""
    if page_og_image and not page_og_image.endswith("no-image.png") and "logo" not in page_og_image.lower():
        if page_og_image.startswith("/"):
            return f"{BASE_URL}{page_og_image}"
        return page_og_image

    img_matches = re.findall(r'src="([^"]+)"', html, re.IGNORECASE)
    for src in img_matches:
        src = src.strip()
        if "no-image" in src or "icon" in src or "banner" in src or "logo" in src:
            continue
        if src.endswith((".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG")):
            if src.startswith("http"):
                return src
            if src.startswith("/"):
                return f"{BASE_URL}{src}"
            return f"{BASE_URL}/{src}"
    return ""


async def find_article_links(page, list_url: str) -> list[str]:
    """Lấy danh sách link bài viết trên trang danh mục."""
    try:
        await page.goto(list_url, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(1_000)
    except Exception as e:
        print(f"    [!] Không thể tải danh mục {list_url}: {e}")
        return []

    links = set()
    for sel in ARTICLE_LINK_SELECTORS:
        handles = await page.query_selector_all(sel)
        for h in handles:
            href = await h.get_attribute("href")
            if not href:
                continue
            href = href.strip()
            if href.startswith("/"):
                href = BASE_URL + href
            elif not href.startswith("http"):
                continue

            # Chỉ lấy bài có đuôi .html và không phải trang danh mục/trang chủ
            if not href.endswith(".html") or href in (BASE_URL, f"{BASE_URL}/", list_url):
                continue
            if "/categories/" in href:
                continue
            links.add(href)
        if links:
            break

    return list(links)


async def scrape_article(page, url: str, category: str) -> dict | None:
    """Cào chi tiết bài viết: tiêu đề, ngày, nội dung HTML, thumbnail, lọc chủ đề."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(800)

        # 1. Tiêu đề
        title = ""
        for sel in ["h1.heading-title", "h1", ".heading-title", "h2.title", ".detail-title"]:
            el = await page.query_selector(sel)
            if el:
                title = (await el.inner_text()).strip()
                if title:
                    break
        if not title:
            el = await page.query_selector("meta[property='og:title']")
            if el:
                title = (await el.get_attribute("content") or "").strip()
        if not title:
            return None

        # 2. Ngày đăng
        created_at = None
        for sel in ["#publishupshow-right", "#publishupshow-bottom", ".date", "time", ".published"]:
            el = await page.query_selector(sel)
            if el:
                txt = await el.inner_text()
                parsed = parse_vn_date(txt)
                if parsed:
                    created_at = parsed
                    break
        if not created_at:
            created_at = now_vn()
        # Lọc bài quá 6 tháng
        six_months_ago = datetime.now(VN_TZ) - timedelta(days=180)
        try:
            article_date = date_parser.parse(created_at)
            if article_date < six_months_ago:
                print(f"    [Bỏ qua - Quá 6 tháng]: {title[:60]}...")
                return None
        except Exception:
            pass

        # 3. Nội dung bài viết
        content = ""
        for sel in CONTENT_SELECTORS:
            el = await page.query_selector(sel)
            if el:
                content = (await el.inner_html()).strip()
                if len(content) > 100:
                    break

        content = fix_image_urls(content)

        # Loại bỏ thẻ h1 và khối ngày cập nhật bị dính trong content để tránh lặp tiêu đề 2 lần
        content = re.sub(r"<h1[^>]*>[\s\S]*?</h1>", "", content, flags=re.IGNORECASE)
        content = re.sub(r'<p[^>]*id=["\']publishupshow-bottom["\'][^>]*>[\s\S]*?</p>', "", content, flags=re.IGNORECASE).strip()

        # 4. Tóm tắt (Summary)
        summary = ""
        p_lead = await page.query_selector(".article-content p strong")
        if p_lead:
            summary = (await p_lead.inner_text()).strip()

        if not summary:
            el_desc = await page.query_selector("meta[name='description'], meta[property='og:description']")
            if el_desc:
                summary = (await el_desc.get_attribute("content") or "").strip()

        if not summary:
            text_only = re.sub(r"<[^>]+>", " ", content)
            text_only = re.sub(r"\s+", " ", text_only).strip()
            summary = text_only[:220] + ("…" if len(text_only) > 220 else "")

        # 5. Lọc chuyên đề: Đất đai và Pháp luật
        if not is_land_or_law_related(title, summary, content):
            print(f"    [Bỏ qua - Không thuộc Đất đai/Pháp luật]: {title[:60]}...")
            return None

        # 6. Ảnh đại diện (Thumbnail)
        og_img = ""
        el_og = await page.query_selector("meta[property='og:image']")
        if el_og:
            og_img = (await el_og.get_attribute("content") or "").strip()
        image = extract_thumbnail(content, og_img)

        slug = make_slug(title)
        return {
            "id": str(uuid.uuid4()),
            "title": title,
            "slug": slug,
            "summary": summary,
            "content": content,
            "image": image,
            "url": url,
            "category": category,
            "created_at": created_at,
            "expired_at": add_days(created_at, 90),
        }
    except Exception as exc:
        print(f"    [!] Lỗi khi cào {url}: {exc}")
        return None


async def next_page_url(page, list_url: str, current_page_num: int) -> str | None:
    """Tạo URL trang kế tiếp."""
    next_page_num = current_page_num + 1
    if "?" in list_url:
        base = list_url.split("?")[0]
        return f"{base}?CurrentPage={next_page_num}"
    return f"{list_url}?CurrentPage={next_page_num}"


async def scrape_section(browser, section: dict) -> list[dict]:
    """Cào bài viết trong danh mục theo số trang cấu hình."""
    page = await browser.new_page()
    category = section["category"]
    results: list[dict] = []
    seen_urls: set[str] = set()

    for page_num in range(1, section["max_pages"] + 1):
        if page_num == 1:
            current_url = section["list_url"]
        else:
            current_url = await next_page_url(page, section["list_url"], page_num - 1)

        print(f"\n  [{category.upper()}] Trang {page_num}: {current_url}")
        links = await find_article_links(page, current_url)
        print(f"    → Tìm được {len(links)} liên kết bài viết")

        if not links:
            break

        for url in links:
            if url in seen_urls:
                continue
            seen_urls.add(url)
            item = await scrape_article(page, url, category)
            if item:
                print(f"    ✓ [Thu thập]: {item['title'][:65]}... (Ảnh: {'Có' if item['image'] else 'Không'})")
                results.append(item)

    await page.close()
    return results


async def main():
    print("=" * 65)
    print("Scraper Tin tức Đất đai & Pháp luật - snnmt.daklak.gov.vn")
    print("=" * 65)

    all_items: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print("Trình duyệt Chromium đã khởi động thành công.")

        for section in SECTIONS:
            print(f"\n{'─'*55}")
            print(f"Bắt đầu thu thập mục: {section['category'].upper()} ({section['list_url']})")
            items = await scrape_section(browser, section)
            all_items.extend(items)
            print(f"  → Đã lưu {len(items)} bài phù hợp từ mục này.")

        await browser.close()

        # Đọc data cũ từ file nếu có
        old_news = []
        if OUTPUT_PATH.exists() and OUTPUT_PATH.stat().st_size > 0:
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                old_news = json.load(f)

    # Lấy danh sách url và slug cũ để so sánh
    old_urls = {item["url"] for item in old_news}
    old_slugs = {item["slug"] for item in old_news}

    # Khử trùng theo slug và chỉ lấy bài mới chưa có trong file
    seen_slugs: set[str] = set()
    new_items: list[dict] = []
    for item in all_items:
        if item["slug"] not in seen_slugs and item["content"]:
            if item["url"] not in old_urls and item["slug"] not in old_slugs:
                seen_slugs.add(item["slug"])
                new_items.append(item)

    if new_items:
        all_news = new_items + old_news  # Tin mới lên đầu
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(all_news, f, ensure_ascii=False, indent=2)
        print(f"\n{'='*65}")
        print(f"HOÀN TẤT! Đã thêm {len(new_items)} bài mới vào {OUTPUT_PATH}")
    else:
        print(f"\n{'='*65}")
        print("Không có bài viết mới nào!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
