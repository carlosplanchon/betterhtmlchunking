import pytest

from betterhtmlchunking.main import DomRepresentation
from betterhtmlchunking.tree_regions_system import ReprLengthComparisionBy


def test_roi_respects_max_length():
    html = "<html><body>" + "".join(f"<p>{'x'*10}</p>" for _ in range(10)) + "</body></html>"
    max_length = 50

    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=max_length,
        website_code=html,
        repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH,
    )
    dom.start()

    rois = dom.tree_regions_system.sorted_roi_by_pos_xpath

    assert len(rois) == 2
    for roi in rois.values():
        assert roi.repr_length <= max_length
