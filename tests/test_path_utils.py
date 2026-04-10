from wiki_path.path_utils import reconstruct_path, normalize_title, format_path


class TestReconstructPath:
    def test_direct_link(self):
        forward = {"source": None, "target": "source"}
        backward = {"target": None}
        assert reconstruct_path("target", forward, backward) == ["source", "target"]

    def test_two_hop_path(self):
        forward = {"source": None, "A": "source"}
        backward = {"target": None, "A": "target"}
        path = reconstruct_path("A", forward, backward)
        assert path == ["source", "A", "target"]

    def test_three_hop_path(self):
        forward = {"source": None, "A": "source", "B": "A"}
        backward = {"target": None, "B": "target"}
        path = reconstruct_path("B", forward, backward)
        assert path == ["source", "A", "B", "target"]

    def test_four_hop_path(self):
        forward = {"source": None, "A": "source", "M": "A"}
        backward = {"target": None, "B": "target", "M": "B"}
        path = reconstruct_path("M", forward, backward)
        assert path == ["source", "A", "M", "B", "target"]

    def test_source_equals_target_via_direct_link(self):
        forward = {"source": None, "target": "source"}
        backward = {"target": None}
        path = reconstruct_path("target", forward, backward)
        assert path[0] == "source"
        assert path[-1] == "target"
        assert len(path) == 2


class TestNormalizeTitle:
    def test_capitalizes_first_letter(self):
        assert normalize_title("calculus") == "Calculus"

    def test_replaces_underscores(self):
        assert normalize_title("Albert_Einstein") == "Albert Einstein"

    def test_strips_whitespace(self):
        assert normalize_title("  Physics  ") == "Physics"

    def test_preserves_case_after_first(self):
        assert normalize_title("iPhone") == "IPhone"

    def test_already_normalized(self):
        assert normalize_title("Albert Einstein") == "Albert Einstein"

    def test_empty_string(self):
        assert normalize_title("") == ""


class TestFormatPath:
    def test_single_article(self):
        result = format_path(["Physics"])
        assert "Physics" in result
        assert "0 hops" in result

    def test_two_articles(self):
        result = format_path(["Physics", "Einstein"])
        assert "→" in result
        assert "1 hop" in result

    def test_three_articles(self):
        result = format_path(["A", "B", "C"])
        assert "2 hops" in result

    def test_empty_path(self):
        result = format_path([])
        assert "No path" in result
