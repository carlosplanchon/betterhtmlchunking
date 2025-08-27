from betterhtmlchunking.main import DomRepresentation
from betterhtmlchunking.tree_regions_system import ReprLengthComparisionBy


def test_large_html_is_split_into_multiple_chunks():
    html = (
        "<html><body>"
        + "".join(f"<p>{'x'*20}</p>" for _ in range(10))
        + "</body></html>"
    )
    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=50,
        website_code=html,
        repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH,
    )
    dom.start()

    chunks = dom.render_system.text_render_roi
    assert len(chunks) > 1
    combined_text = "".join(chunks.values()).replace("\n", "")
    assert len(combined_text) == 200
    for chunk in chunks.values():
        assert len(chunk.replace("\n", "")) <= 50
