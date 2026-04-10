from wiki_path.filters import filter_valid_links, is_valid_article


class TestIsValidArticle:
    def test_normal_article(self):
        assert is_valid_article("Albert Einstein") is True

    def test_empty_string(self):
        assert is_valid_article("") is False

    def test_file_prefix(self):
        assert is_valid_article("File:Photo.jpg") is False

    def test_category_prefix(self):
        assert is_valid_article("Category:Physicists") is False

    def test_template_prefix(self):
        assert is_valid_article("Template:Infobox") is False

    def test_wikipedia_prefix(self):
        assert is_valid_article("Wikipedia:Policies") is False

    def test_help_prefix(self):
        assert is_valid_article("Help:Contents") is False

    def test_talk_prefix(self):
        assert is_valid_article("Talk:Calculus") is False

    def test_user_prefix(self):
        assert is_valid_article("User:JohnDoe") is False

    def test_portal_prefix(self):
        assert is_valid_article("Portal:Mathematics") is False

    def test_draft_prefix(self):
        assert is_valid_article("Draft:New Article") is False

    def test_article_with_parentheses(self):
        assert is_valid_article("Mercury (planet)") is True

    def test_article_with_colon_in_name(self):
        assert is_valid_article("Star Wars: A New Hope") is True


class TestFilterValidLinks:
    def test_keeps_namespace_zero(self):
        raw = [{"ns": 0, "title": "Calculus"}, {"ns": 0, "title": "Physics"}]
        assert filter_valid_links(raw) == ["Calculus", "Physics"]

    def test_drops_non_zero_namespace(self):
        raw = [
            {"ns": 0, "title": "Calculus"},
            {"ns": 14, "title": "Category:Mathematics"},
            {"ns": 6, "title": "File:Diagram.png"},
        ]
        assert filter_valid_links(raw) == ["Calculus"]

    def test_drops_missing_title(self):
        raw = [{"ns": 0, "title": ""}, {"ns": 0, "title": "Physics"}]
        assert filter_valid_links(raw) == ["Physics"]

    def test_empty_input(self):
        assert filter_valid_links([]) == []

    def test_drops_excluded_prefix_in_ns0(self):
        raw = [{"ns": 0, "title": "Wikipedia:Help"}, {"ns": 0, "title": "Normal"}]
        assert filter_valid_links(raw) == ["Normal"]
