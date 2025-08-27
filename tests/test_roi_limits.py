import pytest

from betterhtmlchunking.main import DomRepresentation
from betterhtmlchunking.tree_regions_system import ReprLengthComparisionBy
from typer.testing import CliRunner
from betterhtmlchunking.cli import app


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


def test_small_subtree_becomes_single_roi():
    html = (
        "<html><body><div><p>uno</p><p>dos</p></div><p>tres</p></body></html>"
    )
    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=40,
        website_code=html,
        repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH,
    )
    dom.start()

    rois = dom.tree_regions_system.sorted_roi_by_pos_xpath
    div_roi = None
    for roi in rois.values():
        if roi.pos_xpath_list == ["/html/body/div"]:
            div_roi = roi
            break

    assert div_roi is not None
    assert div_roi.node_is_roi is True


def test_large_leaf_node_emits_warning():
    html = f"<html><body><p>{'x'*100}</p></body></html>"
    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=50,
        website_code=html,
        repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH,
    )

    with pytest.warns(UserWarning):
        dom.start()

    rois = dom.tree_regions_system.sorted_roi_by_pos_xpath
    assert len(rois) == 1
    roi = list(rois.values())[0]
    assert roi.node_is_roi is True
    assert roi.repr_length > 50
    assert roi.pos_xpath_list == ["/html/body/p"]


def test_root_selection_without_html_tag():
    html = "<div><p>hola</p></div>"
    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=50,
        website_code=html,
        repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH,
    )
    dom.start()

    rois = dom.tree_regions_system.sorted_roi_by_pos_xpath
    assert rois
    first_roi = rois[0]
    assert first_roi.pos_xpath_list == ["/div"]


def test_cli_silent_output_html_and_text():
    html = "<html><body><p>uno</p><p>dos</p></body></html>"
    runner = CliRunner()

    result_html = runner.invoke(
        app, ["chunk", "--max-length", "20"], input=html
    )
    assert result_html.exit_code == 0
    assert result_html.stderr == ""

    dom_html = DomRepresentation(
        MAX_NODE_REPR_LENGTH=20,
        website_code=html,
        repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH,
    )
    dom_html.start()
    expected_html = dom_html.render_system.html_render_roi.get(0, "")
    assert result_html.stdout.strip() == expected_html.strip()

    result_text = runner.invoke(
        app, ["chunk", "--max-length", "20", "--text"], input=html
    )
    assert result_text.exit_code == 0
    assert result_text.stderr == ""

    dom_text = DomRepresentation(
        MAX_NODE_REPR_LENGTH=20,
        website_code=html,
        repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH,
    )
    dom_text.start()
    expected_text = dom_text.render_system.html_render_roi.get(0, "")
    assert result_text.stdout.strip() == expected_text.strip()
