"""robots.txt and sitemap.xml, served by the API at the site root.

A single page application is invisible to anything that does not run
JavaScript. Every URL returns the same empty document, so a crawler that
follows no link and executes no script learns that exactly one page exists.
The sitemap is how it learns the others, which makes these two files the
cheapest indexing work available and the first thing a template should ship.

Both are generated from the request rather than from configuration, so a
preview deployment advertises itself and not production. Declare your routes in
STATIC_PATHS; it is the one place the site's shape is written down, and the
prerenderer a growing application eventually needs reads the same list.
"""

from litestar import Request, Response, get

XML_MEDIA_TYPE = "application/xml"
TEXT_MEDIA_TYPE = "text/plain"

STATIC_PATHS = ("/",)
"""Every page a crawler should know about.

One entry per route the SPA answers. A route that is not here is a route search
engines will not find, because no link on a client-rendered page survives
without JavaScript.
"""

DISALLOWED = ("/api/", "/schema")
"""Paths worth keeping out of an index: the API and its documentation.

Not a security measure — robots.txt is a request, not a guard. It keeps a
crawler's budget on the pages that are meant to be read.
"""

CACHE = "public, max-age=3600"
"""An hour. These change when the application does, not by the minute."""


def origin_of(request: Request) -> str:
    """The public origin, honouring the proxy headers nginx sets.

    Taken from the request rather than from configuration so a preview
    deployment, a local run and production each advertise themselves and not
    each other.
    """
    url = request.url
    scheme = request.headers.get("x-forwarded-proto", url.scheme)
    host = request.headers.get("host", url.netloc)
    return f"{scheme}://{host}"


@get(
    "/robots.txt",
    name="seo:robots",
    media_type=TEXT_MEDIA_TYPE,
    include_in_schema=False,
)
async def robots(request: Request) -> Response[str]:
    """Allow the site, keep the API out, and point at the sitemap."""
    lines = ["User-agent: *", "Allow: /"]
    lines += [f"Disallow: {path}" for path in DISALLOWED]
    lines += ["", f"Sitemap: {origin_of(request)}/sitemap.xml", ""]
    return Response(
        "\n".join(lines), media_type=TEXT_MEDIA_TYPE, headers={"Cache-Control": CACHE}
    )


@get(
    "/sitemap.xml",
    name="seo:sitemap",
    media_type=XML_MEDIA_TYPE,
    include_in_schema=False,
)
async def sitemap(request: Request) -> Response[str]:
    """One entry per declared page, absolute, on the origin that was asked."""
    origin = origin_of(request)
    entries = "\n".join(
        f"<url><loc>{origin}{path}</loc></url>" for path in STATIC_PATHS
    )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )
    return Response(body, media_type=XML_MEDIA_TYPE, headers={"Cache-Control": CACHE})
