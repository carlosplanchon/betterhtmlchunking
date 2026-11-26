#!/usr/bin/env python3

import pytest

from betterhtmlchunking.utils import wanted_xpath
from betterhtmlchunking.utils import remove_unwanted_tags
from betterhtmlchunking.tree_representation import DOMTreeRepresentation
from betterhtmlchunking.tree_representation import get_element_text


class TestWantedXPath:
    """Tests for wanted_xpath function."""

    def test_wanted_xpath_with_allowed_tag(self):
        """Test that allowed tags return True."""
        xpath = "/html/body/div"
        tag_list = ["/head", "/script"]
        assert wanted_xpath(xpath, tag_list) is True

    def test_wanted_xpath_with_filtered_tag(self):
        """Test that filtered tags return False."""
        xpath = "/html/head/title"
        tag_list = ["/head", "/script"]
        assert wanted_xpath(xpath, tag_list) is False

    def test_wanted_xpath_with_multiple_filtered_tags(self):
        """Test filtering with multiple unwanted tags."""
        xpath = "/html/body/script"
        tag_list = ["/head", "/script", "/style"]
        assert wanted_xpath(xpath, tag_list) is False

    def test_wanted_xpath_with_empty_filter_list(self):
        """Test that empty filter list allows all tags."""
        xpath = "/html/body/div"
        tag_list = []
        assert wanted_xpath(xpath, tag_list) is True

    @pytest.mark.parametrize("xpath,tag_list,expected", [
        # Entries match whole steps, never a prefix of a longer tag name.
        ("/html/body/header", ["/head"], True),
        ("/html/body", ["/b"], True),
        ("/html/body/pre", ["/p"], True),
        ("/html/body/gallery-item", ["/g"], True),
        # A step without an index matches any position.
        ("/html/body/p[3]", ["/p"], False),
        ("/html/body/svg/g/path", ["/svg"], False),
        # A step with an index matches only that position.
        ("/html/body/div[2]/p", ["/div[2]"], False),
        ("/html/body/div[20]/p", ["/div[2]"], True),
        # Several steps must appear one after the other.
        ("/html/body/aside", ["/body/aside"], False),
        ("/html/body/main/aside", ["/body/aside"], True),
    ])
    def test_wanted_xpath_matches_whole_steps(self, xpath, tag_list, expected):
        assert wanted_xpath(xpath, tag_list) is expected


class TestRemoveUnwantedTags:
    """Tests for remove_unwanted_tags function."""

    def test_remove_script_tags(self):
        """Test removing script tags from tree."""
        html = "<html><body><div>Content</div><script>alert('test')</script></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        filtered_tree = remove_unwanted_tags(
            tree_representation=tree,
            tag_list_to_filter_out=["/script"]
        )

        # Check that script tag is removed
        xpath_strings = [
            node.identifier for node in filtered_tree.tree.all_nodes()
        ]
        assert not any("/script" in xpath for xpath in xpath_strings)

    def test_remove_multiple_tag_types(self):
        """Test removing multiple tag types."""
        html = "<html><head><title>Test</title></head><body><div>Content</div></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        filtered_tree = remove_unwanted_tags(
            tree_representation=tree,
            tag_list_to_filter_out=["/head", "/title"]
        )

        xpath_strings = [
            node.identifier for node in filtered_tree.tree.all_nodes()
        ]
        assert not any("/head" in xpath for xpath in xpath_strings)
        assert not any("/title" in xpath for xpath in xpath_strings)

    def test_remove_unwanted_tags_preserves_wanted_content(self):
        """Test that wanted content is preserved after filtering."""
        html = "<html><body><div>Keep this</div><script>Remove this</script></body></html>"
        tree = DOMTreeRepresentation(website_code=html)

        filtered_tree = remove_unwanted_tags(
            tree_representation=tree,
            tag_list_to_filter_out=["/script"]
        )

        xpath_strings = [node.identifier for node in filtered_tree.tree.all_nodes()]
        assert any("/div" in xpath for xpath in xpath_strings)

    def test_remove_unwanted_tags_keeps_tails(self):
        """The text after a removed element belongs to its parent: keep it."""
        tree = DOMTreeRepresentation(
            website_code="<html><body><p>Hello <script>x()</script> world</p></body></html>"
        )
        remove_unwanted_tags(tree, ["/script"])
        text = get_element_text(tree.root)
        assert "world" in text
        assert "x()" not in text
