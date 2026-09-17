"""Tests for robots.txt and sitemap.xml."""

from litestar import Litestar
from litestar.testing import AsyncTestClient

from backend.seo import DISALLOWED, STATIC_PATHS


class TestSeo:
    async def test_robots_points_at_the_sitemap_on_the_host_asked_for(
        self, client: AsyncTestClient[Litestar]
    ) -> None:
        """A preview deployment advertises itself, not production."""
        response = await client.get("/robots.txt", headers={"host": "preview.example"})
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert "Sitemap: http://preview.example/sitemap.xml" in response.text
        for path in DISALLOWED:
            assert f"Disallow: {path}" in response.text

    async def test_robots_honours_the_proxy_scheme(
        self, client: AsyncTestClient[Litestar]
    ) -> None:
        """Behind nginx the scheme is in a header, not in the URL."""
        response = await client.get(
            "/robots.txt",
            headers={"host": "example.com", "x-forwarded-proto": "https"},
        )
        assert "Sitemap: https://example.com/sitemap.xml" in response.text

    async def test_the_sitemap_lists_every_declared_page(
        self, client: AsyncTestClient[Litestar]
    ) -> None:
        """A route missing from STATIC_PATHS is a route nobody finds."""
        response = await client.get("/sitemap.xml", headers={"host": "example.com"})
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/xml")
        for path in STATIC_PATHS:
            assert f"<loc>http://example.com{path}</loc>" in response.text
        assert response.text.count("<url>") == len(STATIC_PATHS)
