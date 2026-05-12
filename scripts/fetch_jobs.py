#!/usr/bin/env python3
"""Fetch job listings from 104.com.tw via Playwright. Outputs single-line JSON to stdout."""

import argparse
import json
import sys
import time

DETAIL_API = "https://www.104.com.tw/job/ajax/content/{job_code}"
JOB_LINK_RE = r"/job/([A-Za-z0-9]+)$"

# 104 salaryType codes → display label
SALARY_TYPE_LABEL: dict[int, str] = {
    10: "時薪",
    20: "月薪",
    30: "月薪",
    40: "日薪",
    60: "年薪",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def build_search_url(keyword: str, area: str, salary_min=None, salary_max=None, page: int = 1) -> str:
    params = {
        "keyword": keyword, "area": area,
        "ro": "0", "kwop": "7", "order": "15",
        "asc": "0", "page": str(page), "mode": "s",
    }
    if salary_min is not None:
        params["salmin"] = str(salary_min)
    if salary_max is not None:
        params["salmax"] = str(salary_max)
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://www.104.com.tw/jobs/search/?{qs}"


def _salary_desc(low: int, high: int) -> str:
    if low == 0 and high == 0:
        return "面議"
    if high >= 9_990_000:
        return f"月薪 {low:,} 元以上" if low else "面議"
    if low and high:
        return f"月薪 {low:,}–{high:,} 元"
    if low:
        return f"月薪 {low:,} 元以上"
    return "面議"


def _job_code_from_link(link: str) -> str:
    import re
    m = re.search(JOB_LINK_RE, link)
    return m.group(1) if m else ""


# ── Playwright fetch (primary) ────────────────────────────────────────────────

def _fetch_via_playwright(keyword: str, area: str, salary_min, salary_max, limit: int, page: int = 1):
    """Navigate to 104 search page with Playwright, intercept search/api/jobs response."""
    from playwright.sync_api import sync_playwright

    search_url = build_search_url(keyword, area, salary_min, salary_max, page)
    captured: dict = {}
    session_cookies: list = []

    def _handle_route(route):
        req = route.request
        if "search/api/jobs" in req.url:
            try:
                resp = route.fetch()
                body = resp.text()
                captured["jobs_raw"] = json.loads(body)
                captured["status"] = resp.status
            except Exception as exc:
                _log(f"Route fetch error for api/jobs: {exc}")
            finally:
                try:
                    route.fulfill(response=resp)
                except Exception:
                    pass
        else:
            try:
                route.continue_()
            except Exception:
                pass

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        ctx = browser.new_context(
            locale="zh-TW",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = ctx.new_page()
        page.route("**/*", _handle_route)

        try:
            page.goto(search_url, timeout=30_000)
        except Exception as exc:
            _log(f"Page.goto error: {exc}")

        # Wait for api/jobs to be captured (up to 15 s)
        for _ in range(30):
            if "jobs_raw" in captured:
                break
            time.sleep(0.5)

        # Extract cookies for detail requests
        session_cookies = ctx.cookies()
        browser.close()

    if "jobs_raw" not in captured:
        raise RuntimeError("api/jobs response not captured by Playwright")

    raw_list: list = captured["jobs_raw"].get("data", [])[:limit]
    return raw_list, session_cookies


# ── detail fetch ──────────────────────────────────────────────────────────────

def _fetch_detail(job_code: str, cookies: list) -> dict:
    import requests as req_lib

    url = DETAIL_API.format(job_code=job_code)
    cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Referer": f"https://www.104.com.tw/job/{job_code}",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9",
        "Cookie": cookie_header,
    }
    resp = req_lib.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json().get("data", {})
    job_info = data.get("jobDetail", {})
    condition = data.get("condition", {})
    skill_tags = [t.get("description", "") for t in condition.get("skill", [])]

    # Extract salary info from detail (more accurate than list API's salaryLow/High)
    sal_type_code = job_info.get("salaryType")
    sal_label = SALARY_TYPE_LABEL.get(sal_type_code, "月薪")
    sal_min = job_info.get("salaryMin", 0)
    sal_max = job_info.get("salaryMax", 0)
    sal_display = job_info.get("salary", "")  # pre-formatted string e.g. "年薪1,300,000~2,000,000元"
    divisor = 12 if sal_label == "年薪" else 1
    salary_detail = {
        "display": sal_display,
        "type": sal_label,
        "min": sal_min,
        "max": sal_max,
        "monthly_min": sal_min // divisor if sal_min else 0,
        "monthly_max": sal_max // divisor if sal_max else 0,
    } if sal_display else None

    return {
        "jd_text": job_info.get("jobDescription", ""),
        "skill_tags": [s for s in skill_tags if s],
        "exp_required": condition.get("workExp", ""),
        "education": condition.get("edu", ""),
        "salary_detail": salary_detail,
    }


# ── main ──────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch 104 job listings via Playwright")
    p.add_argument("--keyword", required=True)
    p.add_argument("--area", required=True)
    p.add_argument("--salary-min", type=int, default=None)
    p.add_argument("--salary-max", type=int, default=None)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--page", type=int, default=1,
                   help="Page number for 104 search results (1-indexed)")
    p.add_argument("--exclude-negotiable", action="store_true", default=False,
                   help="Exclude jobs with no salary information (面議)")
    p.add_argument("--title-filter", default=None,
                   help="Comma-separated substrings; only jobs whose title contains at least one are kept (case-insensitive)")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    search_url = build_search_url(args.keyword, args.area, args.salary_min, args.salary_max, args.page)
    errors: list[str] = []

    # ── list ──
    try:
        raw_list, session_cookies = _fetch_via_playwright(
            args.keyword, args.area, args.salary_min, args.salary_max, args.limit, args.page
        )
    except Exception as exc:
        _log(f"Playwright list error: {exc}")
        print(json.dumps({
            "status": "need_fallback",
            "search_url": search_url,
            "page": args.page,
            "errors": [str(exc)],
        }, ensure_ascii=False))
        return

    # Apply title filter before expensive detail fetches
    if args.title_filter:
        filters = [f.strip().lower() for f in args.title_filter.split(",") if f.strip()]
        raw_list = [item for item in raw_list
                    if any(f in item.get("jobName", "").lower() for f in filters)]

    # ── details ──
    jobs: list[dict] = []
    for item in raw_list:
        job_link = item.get("link", {}).get("job", "")
        job_code = _job_code_from_link(job_link)
        base = {
            "job_code": job_code,
            "title": item.get("jobName", ""),
            "company": item.get("custName", ""),
            "salary": _salary_desc(item.get("salaryLow", 0), item.get("salaryHigh", 0)),
            "location": item.get("jobAddrNoDesc", ""),
            "url": job_link,
        }
        detail = {"jd_text": "", "skill_tags": [], "exp_required": "", "education": "", "salary_detail": None}
        if job_code:
            try:
                time.sleep(0.4)
                detail = _fetch_detail(job_code, session_cookies)
            except Exception as exc:
                _log(f"Detail error for {job_code}: {exc}")
                errors.append(f"job {job_code}: {exc}")

        # Override salary display with detail's more accurate info (includes 年薪/月薪 label)
        sd = detail.pop("salary_detail", None)
        if sd and sd.get("display"):
            base["salary"] = sd["display"]
            base["salary_type"] = sd["type"]
            base["salary_monthly_min"] = sd["monthly_min"]
            base["salary_monthly_max"] = sd["monthly_max"]
        else:
            base["salary_type"] = "月薪"
            base["salary_monthly_min"] = item.get("salaryLow", 0)
            base["salary_monthly_max"] = item.get("salaryHigh", 0)

        jobs.append({**base, **detail})

    # Apply negotiable salary filter
    if args.exclude_negotiable:
        jobs = [j for j in jobs if j["salary_monthly_max"] > 0]

    print(json.dumps({
        "status": "success",
        "page": args.page,
        "jobs": jobs,
        "errors": errors,
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        _log(f"Fatal: {exc}")
        print(json.dumps({"status": "error", "errors": [str(exc)]}, ensure_ascii=False))
        sys.exit(1)
