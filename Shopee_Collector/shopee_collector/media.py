from __future__ import annotations

import asyncio
from urllib.request import HTTPRedirectHandler


ACCESS_ERRORS = {401, 403, 429}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


async def download_assets(store, kind, fetch, blocked, urls=None):
    """Save each distinct observed asset and stop the pass on access restrictions."""
    if urls is None:
        urls = (link[f"{kind}_url"] for link in store.media_links(kind))
    for url in dict.fromkeys(urls):
        if reason := blocked():
            return reason
        previous = store.get(kind, url) or {}
        path = previous.get("local_path")
        if previous.get("status") == "saved" and path and store.file_saved(previous):
            continue
        if previous.get("status") == "unsupported_stream" or previous.get("http_status") in (404, 410):
            continue
        result = await asyncio.to_thread(fetch, store.folder, url)
        with store.db:
            store.put(kind, url, result)
        if result.get("http_status") in ACCESS_ERRORS:
            return f"{kind}_{result['status']}"
        await asyncio.sleep(0.25)
    return blocked()
