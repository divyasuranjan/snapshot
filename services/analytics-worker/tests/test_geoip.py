import httpx
import pytest
import respx

from app.enrichment.geoip import GeoIPLookup


def make_lookup() -> GeoIPLookup:
    client = httpx.AsyncClient()
    return GeoIPLookup(client=client, timeout_seconds=1.0, cache_size=100, cache_ttl_seconds=60)


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.0.0.5", "192.168.1.1", "::1", "", "not-an-ip"])
async def test_private_or_invalid_ips_skip_network_call(ip):
    lookup = make_lookup()
    with respx.mock:
        result = await lookup.lookup(ip)
    assert result.country is None


@respx.mock
async def test_successful_lookup():
    respx.get("http://ip-api.com/json/8.8.8.8").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "country": "United States",
                "countryCode": "US",
                "regionName": "California",
                "city": "Mountain View",
                "lat": 37.4056,
                "lon": -122.0775,
            },
        )
    )
    lookup = make_lookup()
    result = await lookup.lookup("8.8.8.8")

    assert result.country == "United States"
    assert result.country_code == "US"
    assert result.city == "Mountain View"
    assert result.lat == 37.4056


@respx.mock
async def test_api_failure_status_falls_back_to_unknown():
    respx.get("http://ip-api.com/json/8.8.8.8").mock(
        return_value=httpx.Response(200, json={"status": "fail", "message": "invalid query"})
    )
    lookup = make_lookup()
    result = await lookup.lookup("8.8.8.8")
    assert result.country is None


@respx.mock
async def test_network_error_falls_back_to_unknown():
    respx.get("http://ip-api.com/json/8.8.8.8").mock(side_effect=httpx.ConnectTimeout("timed out"))
    lookup = make_lookup()
    result = await lookup.lookup("8.8.8.8")
    assert result.country is None


@respx.mock
async def test_repeated_lookups_are_cached():
    route = respx.get("http://ip-api.com/json/8.8.8.8").mock(
        return_value=httpx.Response(200, json={"status": "success", "country": "United States"})
    )
    lookup = make_lookup()
    await lookup.lookup("8.8.8.8")
    await lookup.lookup("8.8.8.8")
    await lookup.lookup("8.8.8.8")

    assert route.call_count == 1
