"""Bidirectional BFS for shortest Wikipedia hyperlink paths."""

from typing import Optional, Callable, Awaitable

from .api_client import WikiApiClient
from .path_utils import reconstruct_path


async def find_path(
    source: str,
    target: str,
    client: WikiApiClient,
    max_depth: int = 6,
    progress_callback: Optional[Callable[[int, int, int], Awaitable[None]]] = None,
) -> Optional[list[str]]:
    """Return the shortest path from source to target, or None."""
    if source == target:
        return [source]

    forward_visited: dict[str, Optional[str]] = {source: None}
    forward_depths: dict[str, int] = {source: 0}
    forward_frontier: set[str] = {source}

    backward_visited: dict[str, Optional[str]] = {target: None}
    backward_depths: dict[str, int] = {target: 0}
    backward_frontier: set[str] = {target}

    best_meeting: Optional[str] = None
    best_total_depth: int = 10 ** 9

    for depth in range(max_depth):
        if not forward_frontier or not backward_frontier:
            break

        if progress_callback:
            await progress_callback(depth, len(forward_frontier), len(backward_frontier))

        if len(forward_frontier) <= len(backward_frontier):
            links_map = await client.fetch_links_batch(
                list(forward_frontier), "outbound"
            )
            new_frontier: set[str] = set()

            for node, links in links_map.items():
                node_depth = forward_depths[node]
                for link in links:
                    if link in forward_visited:
                        continue
                    forward_visited[link] = node
                    forward_depths[link] = node_depth + 1
                    new_frontier.add(link)

                    if link in backward_visited:
                        total = forward_depths[link] + backward_depths[link]
                        if total < best_total_depth:
                            best_total_depth = total
                            best_meeting = link

            forward_frontier = new_frontier
        else:
            links_map = await client.fetch_links_batch(
                list(backward_frontier), "inbound"
            )
            new_frontier = set()

            for node, links in links_map.items():
                node_depth = backward_depths[node]
                for link in links:
                    if link in backward_visited:
                        continue
                    backward_visited[link] = node
                    backward_depths[link] = node_depth + 1
                    new_frontier.add(link)

                    if link in forward_visited:
                        total = forward_depths[link] + backward_depths[link]
                        if total < best_total_depth:
                            best_total_depth = total
                            best_meeting = link

            backward_frontier = new_frontier

        if best_meeting is not None:
            break

    if best_meeting is not None:
        return reconstruct_path(best_meeting, forward_visited, backward_visited)
    return None
