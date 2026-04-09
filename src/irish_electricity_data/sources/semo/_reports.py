from dataclasses import dataclass
import datetime as dt
from typing import Any, Union

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
    date: dt.datetime
    date_retention: dt.date


def fetch_report_list(resource_name: str, page_size: int = 500) -> list:
    url: str = "https://reports.sem-o.com/api/v1/documents/static-reports"
    params: dict[str, Union[str, int]] = {
        "DPuG_ID": "EA-001",
        "page_size": page_size,
        "order_by": "DESC",
        "ExcludeDelayedPublication": 0,
        "sort_by": "Date",
        "ResourceName": resource_name
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    try:
        items = payload["items"]
    except KeyError as e:
        raise ValueError("SEMOpx report list response missing 'items'") from e

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
            date=dt.datetime.strptime(item["Date"], "%Y-%m-%dT%H:%M:%S"),
            date_retention=dt.datetime.strptime(item["DateRetention"], "%Y-%m-%d").date()
        ) for item in items
    ]


def list_reports(resource_name: str, page_size: int = 500) -> list[ReportReference]:
    items = fetch_report_list(resource_name, page_size=page_size)
    return parse_report_list(items)


def fetch_report(report_id: str) -> dict[str, Any]:
    url = f"https://reports.sem-o.com/api/v1/documents/{report_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
