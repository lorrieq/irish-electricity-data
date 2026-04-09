from dataclasses import dataclass
import datetime as dt
from typing import Optional, Union

import requests


@dataclass(frozen=True)
class ReportReference:
    id: str
    dpug_id: str
    report_name: str
    group: list[str]
    dynamic: bool
    resource_name: str
    publish_time: dt.datetime
    date: dt.date
    date_retention: dt.date


def fetch_report_list(date_from: dt.date, date_to: dt.date, search_name: Optional[str] = None) -> list:
    url = "https://reports.semopx.com/api/v1/documents/static-reports"
    params: dict[str, Union[str, int]] = {
        "group": "Market Data",
        "date_from": date_from.strftime("%Y-%m-%d"),
        "date_to": date_to.strftime("%Y-%m-%d"),
        "page": 1
    }

    if search_name is not None:
        params["name"] = search_name

    response = requests.get(url, params)
    resp_data = response.json()

    items = resp_data["items"]

    pages = resp_data["pagination"]["totalPages"]
    for page in range(2, pages + 1):
        page_report_list = requests.get(url, {**params, "page": page})
        items += page_report_list.json()["items"]

    return items


def parse_report_list(items: list) -> list[ReportReference]:
    return [
        ReportReference(
            id=item["_id"],
            dpug_id=item["DPuG_ID"],
            report_name=item["ReportName"],
            group=item["Group"],
            dynamic=item["Dynamic"],
            resource_name=item["ResourceName"],
            publish_time=dt.datetime.strptime(item["PublishTime"], "%Y-%m-%dT%H:%M:%S"),
            date=dt.datetime.strptime(item["Date"], "%Y-%m-%d").date(),
            date_retention=dt.datetime.strptime(item["DateRetention"], "%Y-%m-%d").date()
        ) for item in items
    ]

def list_reports(date_from: dt.date, date_to: dt.date, search_name: Optional[str] = None) -> list[ReportReference]:
    items = fetch_report_list(date_from, date_to, search_name)
    return parse_report_list(items)


def fetch_report(report_id: str) -> str:
    url = f"https://reports.semopx.com/documents/{report_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.text()
