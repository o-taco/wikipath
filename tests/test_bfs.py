"""BFS unit tests with a mocked WikiApiClient."""

import pytest
from unittest.mock import MagicMock

from wiki_path.bfs import find_path


def make_client(outbound: dict[str, list[str]], inbound: dict[str, list[str]]):
    client = MagicMock()

    async def fetch_links_batch(titles: list[str], direction: str) -> dict[str, list[str]]:
        link_map = outbound if direction == "outbound" else inbound
        return {title: link_map.get(title, []) for title in titles}

    client.fetch_links_batch = fetch_links_batch
    return client


@pytest.mark.asyncio
async def test_same_source_and_target():
    client = make_client({}, {})
    path = await find_path("A", "A", client)
    assert path == ["A"]


@pytest.mark.asyncio
async def test_direct_link_one_hop():
    client = make_client(
        outbound={"source": ["target", "other"]},
        inbound={"target": ["source"]},
    )
    path = await find_path("source", "target", client)
    assert path == ["source", "target"]


@pytest.mark.asyncio
async def test_two_hop_path():
    client = make_client(
        outbound={"source": ["A"], "A": ["target"]},
        inbound={"target": ["A"], "A": ["source"]},
    )
    path = await find_path("source", "target", client)
    assert path == ["source", "A", "target"]


@pytest.mark.asyncio
async def test_three_hop_path():
    client = make_client(
        outbound={"source": ["A"], "A": ["B"], "B": ["target"]},
        inbound={"target": ["B"], "B": ["A"], "A": ["source"]},
    )
    path = await find_path("source", "target", client)
    assert path == ["source", "A", "B", "target"]
    assert len(path) == 4


@pytest.mark.asyncio
async def test_no_path_found():
    client = make_client(
        outbound={"source": ["A", "B"]},
        inbound={"target": ["X", "Y"]},
    )
    path = await find_path("source", "target", client, max_depth=3)
    assert path is None


@pytest.mark.asyncio
async def test_path_starts_with_source_ends_with_target():
    client = make_client(
        outbound={"source": ["A"], "A": ["B"], "B": ["target"]},
        inbound={"target": ["B"], "B": ["A"], "A": ["source"]},
    )
    path = await find_path("source", "target", client)
    assert path is not None
    assert path[0] == "source"
    assert path[-1] == "target"


@pytest.mark.asyncio
async def test_bidirectional_uses_backward_expansion():
    client = make_client(
        outbound={
            "source": ["A1", "A2", "A3", "A4", "B"],
            "A1": [], "A2": [], "A3": [], "A4": [],
            "B": ["target"],
        },
        inbound={
            "target": ["B"],
            "B": ["source"],
        },
    )
    path = await find_path("source", "target", client)
    assert path is not None
    assert path[0] == "source"
    assert path[-1] == "target"
    assert len(path) == 3


@pytest.mark.asyncio
async def test_chooses_shorter_path_when_multiple_meetings():
    client = make_client(
        outbound={"source": ["M2", "A"], "A": ["B"], "B": ["M1"]},
        inbound={"target": ["M2", "M1"], "M2": ["source"], "M1": ["B"], "B": ["A"], "A": ["source"]},
    )
    path = await find_path("source", "target", client)
    assert path is not None
    assert len(path) == 3
    assert path == ["source", "M2", "target"]


@pytest.mark.asyncio
async def test_respects_max_depth():
    client = make_client(
        outbound={"source": ["A"], "A": ["B"], "B": ["C"], "C": ["target"]},
        inbound={"target": ["C"], "C": ["B"], "B": ["A"], "A": ["source"]},
    )
    path = await find_path("source", "target", client, max_depth=2)
    assert path is None


@pytest.mark.asyncio
async def test_finds_path_at_exact_max_depth():
    client = make_client(
        outbound={"source": ["A"], "A": ["target"]},
        inbound={"target": ["A"], "A": ["source"]},
    )
    path = await find_path("source", "target", client, max_depth=2)
    assert path == ["source", "A", "target"]
