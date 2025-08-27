import pytest

from betterhtmlchunking.utils import wanted_xpath, remove_unwanted_tags
from betterhtmlchunking.tree_representation import DOMTreeRepresentation


def test_wanted_xpath_accepts_path_without_unwanted_tag():
    assert wanted_xpath("/html/body/div", ["/script", "/style"]) is True


def test_wanted_xpath_rejects_path_with_unwanted_tag():
    assert wanted_xpath("/html/body/script", ["/script", "/style"]) is False


def test_remove_unwanted_tags_prunes_tree():
    html = (
        "<html><body><p>keep</p>"
        "<script>alert('x')</script>"
        "<style>p{color:red}</style>"
        "</body></html>"
    )
    tree = DOMTreeRepresentation(website_code=html)
    remove_unwanted_tags(tree, ["/script", "/style"])
    tree.recompute_representation()
    assert "/html/body/p" in tree.pos_xpaths_list
    assert all("/script" not in xp and "/style" not in xp for xp in tree.pos_xpaths_list)


def test_wanted_xpath_does_not_match_partial_names():
    assert wanted_xpath("/html/body/header", ["/head"]) is True


def test_wanted_xpath_handles_indexed_nodes():
    assert wanted_xpath("/html/body/script[1]", ["/script"]) is False
