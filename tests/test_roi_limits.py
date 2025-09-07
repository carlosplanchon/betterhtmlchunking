import pytest

from betterhtmlchunking.main import DomRepresentation
from betterhtmlchunking.tree_regions_system import ReprLengthComparisionBy


def test_roi_warning_and_limits():
    html = "<p>" + "a" * 25 + "</p>"
    max_len = 10
    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=max_len,
        website_code=html,
        repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH,
    )
    with pytest.warns(UserWarning):
        dom.start()
    roi = dom.tree_regions_system.sorted_roi_by_pos_xpath[0]
    assert roi.node_is_roi is True
    assert roi.repr_length > max_len
