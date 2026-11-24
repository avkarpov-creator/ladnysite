#!/usr/bin/env python3
"""Export daily organic search statistics from Yandex Webmaster as CSV."""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API = "https://api.webmaster.yandex.net/v4"
HOST = "https:ladnysite.ru:443"
TOKEN_FILE = Path(__file__).resolve().parents[1] / ".secrets" / "webmaster.token"
PAGE_SIZE = 500
METRICS = {
    "IMPRESSIONS": "impressions",
    "CLICKS": "clicks",
    "CTR": "ctr_percent",
    "POSITION": "position",
}


def request(path, token, payload=None):
    headers = {"Authorization": f"OAuth {token}", "Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json; charset=UTF-8"
        data = json.dumps(payload).encode("utf-8")

    try:
        with urlopen(Request(API + path, data=data, headers=headers), timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        try:
            code = json.load(error).get("error_code")
        except (ValueError, AttributeError):
            code = None
        raise RuntimeError(f"Яндекс Вебмастер: HTTP {error.code} ({code or error.reason})") from None


def analytics(path, token, mode, regions):
    params = {
        "text_indicator": mode,
        "search_location": "WEB_LOCATION",
        "limit": PAGE_SIZE,
        "offset": 0,
    }
    if regions:
        params["region_ids"] = regions

    while True:
        result = request(path, token, params)
        items = result["text_indicator_to_statistics"]
        yield from items
        params["offset"] += len(items)
        if params["offset"] >= result["count"]:
            return
        if not items:
            raise RuntimeError("API вернул пустую страницу до конца списка.")


def csv_rows(items, mode):
    for item in items:
        primary = item["text_indicator"]["value"]
        complementary = (item.get("popular_complementary_indicator") or {}).get("value", "")
        by_date = defaultdict(dict)
        for statistic in item["statistics"]:
            metric = METRICS.get(statistic["field"])
            if metric:
                by_date[statistic["date"]][metric] = statistic["value"]

        for date, metrics in sorted(by_date.items()):
            yield {
                "date": date,
                "query": primary if mode == "QUERY" else "",
                "url": primary if mode == "URL" else "",
                "popular_url": complementary if mode == "QUERY" else "",
                "popular_query": complementary if mode == "URL" else "",
                **metrics,
            }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--by", choices=("query", "url"), default="query")
    parser.add_argument("--region", type=int, action="append", help="Yandex region ID, repeatable")
    args = parser.parse_args()

    try:
        token = TOKEN_FILE.read_text(encoding="utf-8-sig").strip() if TOKEN_FILE.is_file() else ""
        if not token:
            token = os.environ.get("YANDEX_WEBMASTER_TOKEN", "").strip()
        if not token:
            raise RuntimeError(f"Сохраните OAuth-токен в {TOKEN_FILE}.")
        user_id = int(request("/user", token)["user_id"])
        path = f"/user/{user_id}/hosts/{quote(HOST, safe='')}/query-analytics/list"
        mode = args.by.upper()
        rows = list(csv_rows(analytics(path, token, mode, args.region), mode))
    except (OSError, URLError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print(f"Ошибка выгрузки: {error}", file=sys.stderr)
        return 1

    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=["date", "query", "url", "popular_url", "popular_query", *METRICS.values()],
    )
    writer.writeheader()
    writer.writerows(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
