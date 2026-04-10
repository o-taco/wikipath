"""Integration tests against the live Wikipedia API."""

import pytest
from wiki_path.api_client import WikiApiClient


@pytest.mark.asyncio
async def test_resolve_known_article():
    async with WikiApiClient() as client:
        title, exists, is_disambig = await client.resolve_title("Albert Einstein")
    assert exists is True
    assert title == "Albert Einstein"
    assert is_disambig is False


@pytest.mark.asyncio
async def test_resolve_redirect():
    async with WikiApiClient() as client:
        title, exists, is_disambig = await client.resolve_title("USA")
    assert exists is True
    assert "United States" in title


@pytest.mark.asyncio
async def test_resolve_nonexistent_article():
    async with WikiApiClient() as client:
        _, exists, _ = await client.resolve_title("ZZZThisArticleDoesNotExist12345")
    assert exists is False


@pytest.mark.asyncio
async def test_resolve_disambiguation_page():
    async with WikiApiClient() as client:
        title, exists, is_disambig = await client.resolve_title("Mercury")
    assert exists is True
    assert is_disambig is True


@pytest.mark.asyncio
async def test_fetch_outbound_links_returns_list():
    async with WikiApiClient() as client:
        links = await client.fetch_outbound_links("Calculus")
    assert isinstance(links, list)
    assert len(links) > 0
    assert all(isinstance(t, str) for t in links)


@pytest.mark.asyncio
async def test_fetch_outbound_links_contains_known_link():
    async with WikiApiClient() as client:
        links = await client.fetch_outbound_links("Albert Einstein")
    assert "General relativity" in links
    assert "Special relativity" in links


@pytest.mark.asyncio
async def test_fetch_outbound_links_no_namespace_pollution():
    async with WikiApiClient() as client:
        links = await client.fetch_outbound_links("Calculus")
    for title in links:
        assert not title.startswith("Category:")
        assert not title.startswith("File:")
        assert not title.startswith("Template:")
        assert not title.startswith("Wikipedia:")


@pytest.mark.asyncio
async def test_fetch_inbound_links_returns_list():
    async with WikiApiClient() as client:
        links = await client.fetch_inbound_links("Albert Einstein")
    assert isinstance(links, list)
    assert len(links) > 0


@pytest.mark.asyncio
async def test_fetch_inbound_links_no_namespace_pollution():
    async with WikiApiClient() as client:
        links = await client.fetch_inbound_links("Calculus")
    for title in links:
        assert not title.startswith("Category:")
        assert not title.startswith("File:")


@pytest.mark.asyncio
async def test_link_cache_is_reused():
    async with WikiApiClient() as client:
        links1 = await client.fetch_outbound_links("Calculus")
        links2 = await client.fetch_outbound_links("Calculus")
    assert links1 is links2


@pytest.mark.asyncio
async def test_fetch_links_batch_outbound():
    async with WikiApiClient() as client:
        batch = await client.fetch_links_batch(["Calculus", "Physics"], "outbound")
    assert "Calculus" in batch
    assert "Physics" in batch
    assert isinstance(batch["Calculus"], list)
    assert len(batch["Calculus"]) > 0


@pytest.mark.asyncio
async def test_fetch_links_batch_empty_titles():
    async with WikiApiClient() as client:
        batch = await client.fetch_links_batch([], "outbound")
    assert batch == {}
