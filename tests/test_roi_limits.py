import pytest

from betterhtmlchunking import DomRepresentation
from betterhtmlchunking.main import ReprLengthComparisionBy


def test_div_with_two_small_paragraphs_is_single_roi():
    html_content = "<html><body><div><p>a</p><p>b</p></div></body></html>"
    total_length = len("a") + len("b")
    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=total_length + 1,
        website_code=html_content,
        repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH,
    )
    dom.start()
    sorted_roi = dom.tree_regions_system.sorted_roi_by_pos_xpath
    assert len(sorted_roi) == 1
    roi = next(iter(sorted_roi.values()))
    assert roi.node_is_roi is True
    assert roi.pos_xpath_list == ["/html/body/div"]
