#!/usr/bin/env python3
import os
import sys
import time
import csv
import json
from typing import Dict, List, Optional, Tuple

# --------- PA-API (Product Advertising API v5) ---------
# Official SDK name on PyPI: paapi5-python-sdk
try:
    from paapi5_python_sdk.api.default_api import DefaultApi as PaapiDefaultApi
    from paapi5_python_sdk.models.get_variations_request import GetVariationsRequest  # noqa: F401 (reserved for future)
    from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
    from paapi5_python_sdk.configuration import Configuration as PaapiConfiguration
    from paapi5_python_sdk.models import Condition
except Exception:
    PaapiDefaultApi = None

# --------- SP-API (Selling Partner API) ---------
# Community SDK: python-amazon-sp-api (sp-api)
try:
    from sp_api.base import Marketplaces
    from sp_api.api import ProductPricing
    from sp_api.base import SellingApiBadRequestException
except Exception:
    ProductPricing = None


# Basic category mappings for PA-API SearchItems SearchIndex for US marketplace
PAAPI_CATEGORY_MAP = {
    # Input name -> SearchIndex
    "Arts,Crafts&Sewing": "ArtsAndCrafts",
    "Clothing,Shoes&Jewelry": "FashionAndAccessories",
    # Add more as needed:
    # "Beauty&PersonalCare": "Beauty",
    # "Toys&Games": "ToysAndGames",
}


def getenv_or_exit(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def build_paapi_client() -> PaapiDefaultApi:
    if PaapiDefaultApi is None:
        print("paapi5-python-sdk is not installed. Please install dependencies.", file=sys.stderr)
        sys.exit(1)

    access_key = getenv_or_exit("PAAPI_ACCESS_KEY")
    secret_key = getenv_or_exit("PAAPI_SECRET_KEY")
    partner_tag = getenv_or_exit("PAAPI_PARTNER_TAG")
    host = os.getenv("PAAPI_HOST", "webservices.amazon.com")

    # Configure PA-API client
    config = PaapiConfiguration()
    config.access_key = access_key
    config.secret_key = secret_key
    config.host = host
    config.partner_tag = partner_tag
    config.partner_type = "Associates"
    return PaapiDefaultApi(PaapiDefaultApi.get_api_client(config))


def marketplace_from_code(code: str):
    # Map SP-API marketplace code to enum
    # Default to US
    mapping = {
        "US": Marketplaces.US,
        "GB": Marketplaces.UK,
        "UK": Marketplaces.UK,
        "DE": Marketplaces.DE,
        "JP": Marketplaces.JP,
        "CA": Marketplaces.CA,
        "FR": Marketplaces.FR,
        "IT": Marketplaces.IT,
        "ES": Marketplaces.ES,
        "IN": Marketplaces.IN,
        "AU": Marketplaces.AU,
        "MX": Marketplaces.MX,
    }
    return mapping.get(code.upper(), Marketplaces.US)


def build_spapi_pricing_client(marketplace_code: str) -> Optional[ProductPricing]:
    if ProductPricing is None:
        print("sp-api is not installed. FBA determination will be skipped.", file=sys.stderr)
        return None

    # sp-api reads creds from env vars documented here:
    # https://github.com/saleweaver/python-amazon-sp-api
    # Required: LWA_APP_ID, LWA_CLIENT_SECRET, SP_API_REFRESH_TOKEN, AWS_ACCESS_KEY, AWS_SECRET_KEY, ROLE_ARN
    required = [
        "LWA_APP_ID",
        "LWA_CLIENT_SECRET",
        "SP_API_REFRESH_TOKEN",
        "AWS_ACCESS_KEY",
        "AWS_SECRET_KEY",
        "ROLE_ARN",
    ]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(
            "Missing SP-API environment variables: " + ", ".join(missing) + ". FBA determination will be skipped.",
            file=sys.stderr,
        )
        return None

    mkt = marketplace_from_code(marketplace_code)
    return ProductPricing(marketplace=mkt)


def search_newest_items(
    client: PaapiDefaultApi,
    category_name: str,
    marketplace_host: str,
    max_pages: int = 1,
    pause_seconds: float = 1.0,
) -> List[Dict]:
    """Search newest arrivals for a PA-API SearchIndex category.

    Returns a list of dicts with keys: asin, title, image, description.
    """
    search_index = PAAPI_CATEGORY_MAP.get(category_name)
    if not search_index:
        raise ValueError(
            f"Unsupported category '{category_name}'. Supported: {list(PAAPI_CATEGORY_MAP.keys())}"
        )

    collected: List[Dict] = []
    for page in range(1, max_pages + 1):
        req = SearchItemsRequest(
            PartnerTag=client.api_client.configuration.partner_tag,
            PartnerType=client.api_client.configuration.partner_type,
            Marketplace=marketplace_host,
            SearchIndex=search_index,
            ItemCount=10,
            ItemPage=page,
            SortBy="NewestArrivals",
            Resources=[
                "Images.Primary.Large",
                "ItemInfo.Title",
                "ItemInfo.Features",
                "ItemInfo.ByLineInfo",
                "ItemInfo.ProductInfo",
                "ItemInfo.ContentInfo",
                "ItemInfo.Classifications",
            ],
        )

        resp = client.search_items(req)
        items = (resp.search_result.items if getattr(resp, "search_result", None) else []) or []
        for it in items:
            asin = getattr(it, "asin", None)
            title = None
            image_url = None
            description = None

            try:
                title = (
                    getattr(it.item_info.title, "display_value", None) if getattr(it, "item_info", None) else None
                )
            except Exception:
                pass

            try:
                image_url = (
                    getattr(it.images.primary.large, "url", None) if getattr(it, "images", None) else None
                )
            except Exception:
                pass

            # Use features list as a pseudo description if available
            try:
                features = (
                    getattr(it.item_info.features, "display_values", None)
                    if getattr(it, "item_info", None)
                    else None
                )
                if isinstance(features, list) and features:
                    description = " " .join(features)[:2000]
            except Exception:
                pass

            if asin:
                collected.append(
                    {
                        "asin": asin,
                        "title": title,
                        "image": image_url,
                        "description": description,
                    }
                )

        time.sleep(pause_seconds)

    return collected


def determine_fba_status(pricing_client: Optional[ProductPricing], marketplace_id: str, asin: str) -> Optional[bool]:
    """Returns True if AFN (FBA), False if MFN (FBM), None if unknown."""
    if pricing_client is None:
        return None
    try:
        # ProductPricing.get_item_offers requires ItemCondition and ASIN
        res = pricing_client.get_item_offers(
            ItemCondition="New",
            Asin=asin,
            MarketplaceId=marketplace_id,
        )
        data = res.payload or {}
        offers = data.get("Offers") or []
        # If any offer is AFN => FBA available
        for offer in offers:
            fulfillment = offer.get("FulfillmentType")
            if fulfillment == "AFN":
                return True
        # If we saw offers and none AFN, assume FBM
        if offers:
            return False
        return None
    except SellingApiBadRequestException as e:
        # Some ASINs may not have offers or be restricted
        sys.stderr.write(f"SP-API get_item_offers error for {asin}: {e}\n")
        return None
    except Exception as e:
        sys.stderr.write(f"SP-API error for {asin}: {e}\n")
        return None


def save_outputs(records: List[Dict], out_csv: str, out_json: str) -> None:
    # JSON
    with open(out_json, "w", encoding="utf-8") as jf:
        json.dump(records, jf, ensure_ascii=False, indent=2)

    # CSV
    fieldnames = ["asin", "title", "image", "description", "is_fba"]
    with open(out_csv, "w", encoding="utf-8", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k) for k in fieldnames})


def main():
    # Inputs
    if len(sys.argv) < 2:
        print(
            "Usage: python fetch_new_products.py '<CategoryName>' [pages] [marketplace]",
            file=sys.stderr,
        )
        print(
            "Example: python fetch_new_products.py 'Arts,Crafts&Sewing' 2 US",
            file=sys.stderr,
        )
        sys.exit(1)

    category_name = sys.argv[1]
    pages = int(sys.argv[2]) if len(sys.argv) >= 3 else 1
    marketplace_code = sys.argv[3] if len(sys.argv) >= 4 else "US"

    # PA-API marketplace host and SP-API marketplace id/code mapping
    # For US:
    paapi_host_by_code = {
        "US": "www.amazon.com",
        "UK": "www.amazon.co.uk",
        "GB": "www.amazon.co.uk",
        "DE": "www.amazon.de",
        "JP": "www.amazon.co.jp",
        "CA": "www.amazon.ca",
        "FR": "www.amazon.fr",
        "IT": "www.amazon.it",
        "ES": "www.amazon.es",
        "IN": "www.amazon.in",
        "AU": "www.amazon.com.au",
        "MX": "www.amazon.com.mx",
    }
    spapi_marketplace_id_by_code = {
        "US": "ATVPDKIKX0DER",
        "UK": "A1F83G8C2ARO7P",
        "GB": "A1F83G8C2ARO7P",
        "DE": "A1PA6795UKMFR9",
        "JP": "A1VC38T7YXB528",
        "CA": "A2EUQ1WTGCTBG2",
        "FR": "A13V1IB3VIYZZH",
        "IT": "APJ6JRA9NG5V4",
        "ES": "A1RKKUPIHCS9HS",
        "IN": "A21TJRUUN4KGV",
        "AU": "A39IBJ37TRP1C6",
        "MX": "A1AM78C64UM0Y8",
    }

    marketplace_host = paapi_host_by_code.get(marketplace_code.upper(), "www.amazon.com")
    marketplace_id = spapi_marketplace_id_by_code.get(marketplace_code.upper(), "ATVPDKIKX0DER")

    paapi_client = build_paapi_client()
    spapi_pricing = build_spapi_pricing_client(marketplace_code)

    items = search_newest_items(
        client=paapi_client,
        category_name=category_name,
        marketplace_host=marketplace_host,
        max_pages=pages,
        pause_seconds=1.0,
    )

    results: List[Dict] = []
    for it in items:
        asin = it["asin"]
        is_fba = determine_fba_status(spapi_pricing, marketplace_id, asin)
        enriched = {**it, "is_fba": is_fba}
        results.append(enriched)

    out_base = f"new_products_{category_name.replace(',', '_').replace('&', 'and').replace(' ', '')}_{marketplace_code}"
    out_csv = out_base + ".csv"
    out_json = out_base + ".json"
    save_outputs(results, out_csv, out_json)

    print(f"Saved {len(results)} items to {out_csv} and {out_json}")


if __name__ == "__main__":
    main()


