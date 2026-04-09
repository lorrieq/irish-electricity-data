from enum import StrEnum

from irish_electricity_data.sources.semo._reports import list_reports


class Auction(StrEnum):
    DAY_AHEAD = "DAY_AHEAD"
    IDA1 = "IDA1"
    IDA2 = "IDA2"
    IDA3 = "IDA3"


_RESOURCE_NAME_BY_AUCTION: dict[Auction, str] = {
    Auction.DAY_AHEAD: "MarketResult_SEM-DA_PWR-MRC-D",
    Auction.IDA1: "MarketResult_SEM-IDA1_PWR-SEM-GB-D",
    Auction.IDA2: "MarketResult_SEM-IDA2_PWR-SEM-GB-D_",
    Auction.IDA3: "MarketResult_SEM-IDA3_PWR-SEM-D_"
}

def _resource_name_for_auction(auction: Auction) -> str:
    return _RESOURCE_NAME_BY_AUCTION[auction]


def get_auction_results(auction: Auction, page_size: int = 500) -> list[dict[str, str]]:
    resource_name = _resource_name_for_auction(auction)
    payload = list_reports(resource_name, page_size=page_size)
    return payload


if __name__ == "__main__":
    print(get_auction_results(Auction.IDA3))
