#!/usr/bin/env python3
"""Fetch job listings from 104.com.tw unofficial JSON API. Outputs single-line JSON to stdout."""

import argparse
import json
import sys
import time

import requests

LIST_API = "https://www.104.com.tw/jobs/search/list"
DETAIL_API = "https://www.104.com.tw/job/ajax/content/{job_code}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.104.com.tw/jobs/search/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def build_search_url(keyword: str, area: str, salary_min=None, salary_max=None) -> str:
    params = {
        "keyword": keyword,
        "area": area,
        "ro": "0", "kwop": "7", "order": "15",
        "asc": "0", "page": "1", "mode": "s",
    }
    if salary_min is not None:
        params["salmin"] = str(salary_min)
    if salary_max is not None:
        params["salmax"] = str(salary_max)
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://www.104.com.tw/jobs/search/?{qs}"


def fetch_job_list(keyword: str, area: str, salary_min=None, salary_max=None, limit: int = 10) -> list:
    params = {
        "keyword": keyword, "area": area,
        "ro": "0", "kwop": "7", "order": "15",
        "asc": "0", "page": "1", "mode": "s",
        "jobsource": "2018indexpoc",
        "pagesize": str(min(limit, 20)),
    }
    if salary_min is not None:
        params["salmin"] = str(salary_min)
    if salary_max is not None:
        params["salmax"] = str(salary_max)
    resp = requests.get(LIST_API, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json().get("data", {}).get("list", [])[:limit]


def fetch_job_detail(job_code: str) -> dict:
    url = DETAIL_API.format(job_code=job_code)
    resp = requests.get(url, headers=HEADERS, timeout=8)
    resp.raise_for_status()
    return resp.json().get("data", {})


def parse_job_list_item(item: dict) -> dict:
    return {
        "job_code": item.get("jobNo", ""),
        "title": item.get("jobName", ""),
        "company": item.get("custName", ""),
        "salary": item.get("salaryDesc", ""),
        "location": item.get("jobAddrNoDesc", ""),
    }


def parse_job_detail(detail: dict) -> dict:
    job_info = detail.get("jobDetail", {})
    condition = detail.get("condition", {})
    skill_tags = [tag.get("description", "") for tag in condition.get("skill", [])]
    return {
        "jd_text": job_info.get("jobDescription", ""),
        "skill_tags": [s for s in skill_tags if s],
        "exp_required": condition.get("workExp", ""),
        "education": condition.get("edu", ""),
    }


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch 104 job listings")
    p.add_argument("--keyword", required=True)
    p.add_argument("--area", required=True)
    p.add_argument("--salary-min", type=int, default=None)
    p.add_argument("--salary-max", type=int, default=None)
    p.add_argument("--limit", type=int, default=10)
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    search_url = build_search_url(args.keyword, args.area, args.salary_min, args.salary_max)
    errors = []

    try:
        raw_list = fetch_job_list(
            args.keyword, args.area,
            args.salary_min, args.salary_max, args.limit,
        )
    except Exception as exc:
        _log(f"List API error: {exc}")
        print(json.dumps({
            "status": "need_fallback",
            "search_url": search_url,
            "errors": [str(exc)],
        }, ensure_ascii=False))
        return

    jobs = []
    for item in raw_list:
        base = parse_job_list_item(item)
        job_code = base["job_code"]
        try:
            time.sleep(0.5)
            detail_raw = fetch_job_detail(job_code)
            detail = parse_job_detail(detail_raw)
        except Exception as exc:
            _log(f"Detail error for {job_code}: {exc}")
            errors.append(f"job {job_code}: {exc}")
            detail = {"jd_text": "", "skill_tags": [], "exp_required": "", "education": ""}
        jobs.append({**base, **detail})

    print(json.dumps({
        "status": "success",
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
