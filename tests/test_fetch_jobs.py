import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import fetch_jobs


# ── 純函式測試（不需 HTTP）───────────────────────────────────────────────────

def test_build_search_url_no_salary():
    url = fetch_jobs.build_search_url("前端工程師", "6001001000")
    assert "6001001000" in url
    assert "salmin" not in url


def test_build_search_url_with_salary():
    url = fetch_jobs.build_search_url("工程師", "6001001000", salary_min=40, salary_max=60)
    assert "salmin=40" in url
    assert "salmax=60" in url


def test_parse_job_list_item_full():
    raw = {
        "jobNo": "abc123",
        "jobName": "前端工程師",
        "custName": "測試科技",
        "salaryDesc": "月薪 50,000",
        "jobAddrNoDesc": "台北市",
    }
    result = fetch_jobs.parse_job_list_item(raw)
    assert result["job_code"] == "abc123"
    assert result["title"] == "前端工程師"
    assert result["company"] == "測試科技"
    assert result["salary"] == "月薪 50,000"
    assert result["location"] == "台北市"


def test_parse_job_list_item_missing_fields():
    """缺少欄位時應回傳空字串，不 raise。"""
    result = fetch_jobs.parse_job_list_item({})
    assert result["job_code"] == ""
    assert result["title"] == ""


def test_parse_job_detail_full():
    raw = {
        "jobDetail": {"jobDescription": "我們需要一位前端工程師..."},
        "condition": {
            "workExp": "3年以上",
            "edu": "大學",
            "skill": [{"description": "React"}, {"description": "TypeScript"}],
        },
    }
    result = fetch_jobs.parse_job_detail(raw)
    assert result["jd_text"] == "我們需要一位前端工程師..."
    assert "React" in result["skill_tags"]
    assert "TypeScript" in result["skill_tags"]
    assert result["exp_required"] == "3年以上"
    assert result["education"] == "大學"


def test_parse_job_detail_empty_skills():
    raw = {"jobDetail": {"jobDescription": "JD"}, "condition": {"skill": []}}
    result = fetch_jobs.parse_job_detail(raw)
    assert result["skill_tags"] == []


# ── main() 測試（mock requests.get）────────────────────────────────────────

def _make_list_response(jobs: list) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"data": {"list": jobs}}
    return resp


def _make_detail_response(job_desc: str = "JD文字") -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "data": {
            "jobDetail": {"jobDescription": job_desc},
            "condition": {"workExp": "2年以上", "edu": "大學", "skill": []},
        }
    }
    return resp


def test_main_success_output_shape(capsys):
    mock_job = {
        "jobNo": "x1", "jobName": "前端工程師",
        "custName": "A公司", "salaryDesc": "面議", "jobAddrNoDesc": "台北市",
    }
    with patch("fetch_jobs.requests.get") as mock_get, \
         patch("fetch_jobs.time.sleep"):
        mock_get.side_effect = [
            _make_list_response([mock_job]),
            _make_detail_response("職務說明內容"),
        ]
        with patch("sys.argv", ["fetch_jobs.py", "--keyword", "前端工程師", "--area", "6001001000"]):
            fetch_jobs.main()

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    assert len(out["jobs"]) == 1
    assert out["jobs"][0]["title"] == "前端工程師"
    assert out["jobs"][0]["jd_text"] == "職務說明內容"
    assert "errors" in out


def test_main_fallback_on_http_error(capsys):
    import requests as req_lib
    with patch("fetch_jobs.requests.get") as mock_get:
        err = req_lib.exceptions.HTTPError("403 Client Error")
        mock_get.side_effect = err
        with patch("sys.argv", ["fetch_jobs.py", "--keyword", "前端工程師", "--area", "6001001000"]):
            fetch_jobs.main()

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "need_fallback"
    assert "search_url" in out
    assert len(out["errors"]) > 0


def test_main_detail_error_still_returns_base(capsys):
    """個別 JD 抓取失敗時，基本資訊仍回傳（jd_text 為空），不中斷整體。"""
    import requests as req_lib
    mock_job = {
        "jobNo": "x1", "jobName": "前端工程師",
        "custName": "A公司", "salaryDesc": "面議", "jobAddrNoDesc": "台北市",
    }
    with patch("fetch_jobs.requests.get") as mock_get, \
         patch("fetch_jobs.time.sleep"):
        mock_get.side_effect = [
            _make_list_response([mock_job]),
            req_lib.exceptions.HTTPError("500"),
        ]
        with patch("sys.argv", ["fetch_jobs.py", "--keyword", "前端工程師", "--area", "6001001000"]):
            fetch_jobs.main()

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    assert out["jobs"][0]["jd_text"] == ""
    assert len(out["errors"]) > 0


def test_stdout_single_json_line(capsys):
    """stdout 必須只有一行 JSON，stderr 不混入。"""
    mock_job = {
        "jobNo": "x1", "jobName": "前端工程師",
        "custName": "A公司", "salaryDesc": "面議", "jobAddrNoDesc": "台北市",
    }
    with patch("fetch_jobs.requests.get") as mock_get, \
         patch("fetch_jobs.time.sleep"):
        mock_get.side_effect = [
            _make_list_response([mock_job]),
            _make_detail_response(),
        ]
        with patch("sys.argv", ["fetch_jobs.py", "--keyword", "前端工程師", "--area", "6001001000"]):
            fetch_jobs.main()

    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    assert len(lines) == 1
    json.loads(lines[0])  # must not raise


def test_main_block_ensure_ascii_in_json_dumps():
    """確認 __main__ 的 ensure_ascii=False 在 json.dumps 內，不是 print 的參數。"""
    import inspect
    import scripts.fetch_jobs as fj
    src = inspect.getsource(fj)
    # 找到 __main__ 區塊的 ensure_ascii 用法
    # 正確：json.dumps({...}, ensure_ascii=False))
    # 錯誤：json.dumps({...}), ensure_ascii=False)
    import re
    bad_pattern = r'json\.dumps\([^)]+\)\s*,\s*ensure_ascii=False'
    assert not re.search(bad_pattern, src), "ensure_ascii=False must be inside json.dumps(), not print()"
