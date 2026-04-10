"""Path reconstruction and display utilities."""


def reconstruct_path(
    meeting_node: str,
    forward_visited: dict[str, str | None],
    backward_visited: dict[str, str | None],
) -> list[str]:
    forward_path: list[str] = []
    node: str | None = meeting_node
    while node is not None:
        forward_path.append(node)
        node = forward_visited.get(node)
    forward_path.reverse()

    backward_path: list[str] = []
    node = backward_visited.get(meeting_node)
    while node is not None:
        backward_path.append(node)
        node = backward_visited.get(node)

    return forward_path + backward_path


def normalize_title(title: str) -> str:
    title = title.strip().replace("_", " ")
    if title:
        title = title[0].upper() + title[1:]
    return title


def format_path(path: list[str]) -> str:
    if not path:
        return "No path found."
    hops = len(path) - 1
    chain = " → ".join(path)
    hop_word = "hop" if hops == 1 else "hops"
    return f"{chain}\n({hops} {hop_word})"
