import betterhtmlchunking.cli as cli
from betterhtmlchunking.main import DomRepresentation, ReprLengthComparisionBy
from typer.testing import CliRunner


def test_chunk_html_stdout_contains_roi_and_stderr_empty():
    html_input = "<html><body><p>first</p><p>second</p></body></html>"
    runner = CliRunner()
    result = runner.invoke(cli.app, ["chunk"], input=html_input)
    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=32768,
        website_code=html_input,
        repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH,
    )
    dom.start()
    expected = dom.render_system.html_render_roi.get(0, "")
    assert result.exit_code == 0
    assert result.stdout == expected + "\n"
    assert result.stderr == ""


def test_chunk_text_stdout_contains_roi_and_stderr_empty():
    html_input = "<html><body><p>first</p><p>second</p></body></html>"
    runner = CliRunner()
    result = runner.invoke(cli.app, ["chunk", "--text"], input=html_input)
    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=32768,
        website_code=html_input,
        repr_length_compared_by=ReprLengthComparisionBy.TEXT_LENGTH,
    )
    dom.start()
    expected = dom.render_system.text_render_roi.get(0, "")
    assert result.exit_code == 0
    assert result.stdout == expected + "\n"
    assert result.stderr == ""
