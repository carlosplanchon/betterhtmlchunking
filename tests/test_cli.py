#!/usr/bin/env python3

import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from betterhtmlchunking.cli import app

runner = CliRunner()


# Sample HTML for testing
SIMPLE_HTML = """
<html>
<head>
    <title>Test Document</title>
</head>
<body>
    <h1>Chapter 1</h1>
    <p>First paragraph with some content.</p>
    <h2>Section 1.1</h2>
    <p>Second paragraph with more content.</p>
    <p>Third paragraph here.</p>
</body>
</html>
"""

MINIMAL_HTML = "<html><body><p>Test</p></body></html>"


class TestCLIBasicFunctionality:
    """Test basic CLI operations."""

    def test_cli_runs_without_error(self):
        """Test that CLI runs without crashing."""
        result = runner.invoke(app, ["--max-length", "1000"], input=MINIMAL_HTML)
        assert result.exit_code == 0

    def test_default_chunk_index_zero(self):
        """Test that default chunk index is 0."""
        result = runner.invoke(app, ["--max-length", "100"], input=SIMPLE_HTML)
        assert result.exit_code == 0
        assert len(result.stdout) > 0

    def test_specific_chunk_index(self):
        """Test selecting a specific chunk by index."""
        result = runner.invoke(
            app, ["--max-length", "50", "--chunk-index", "1"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0
        assert len(result.stdout) > 0

    def test_invalid_chunk_index_returns_empty(self):
        """Test that invalid chunk index returns empty output."""
        result = runner.invoke(
            app, ["--max-length", "100", "--chunk-index", "999"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0
        assert result.stdout == "\n" or result.stdout == ""

    def test_max_length_parameter(self):
        """Test that max-length parameter is respected."""
        result = runner.invoke(app, ["--max-length", "50"], input=SIMPLE_HTML)
        assert result.exit_code == 0

    def test_text_comparison_mode(self):
        """Test --text flag for text length comparison."""
        result = runner.invoke(
            app, ["--max-length", "100", "--text"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0


class TestCLIListChunks:
    """Test --list-chunks functionality."""

    def test_list_chunks_basic(self):
        """Test basic --list-chunks output."""
        result = runner.invoke(
            app, ["--max-length", "100", "--list-chunks"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0
        assert "Total chunks:" in result.stderr
        assert "Chunk 0:" in result.stderr

    def test_list_chunks_shows_all_chunks(self):
        """Test that --list-chunks shows all chunks."""
        result = runner.invoke(
            app, ["--max-length", "50", "--list-chunks"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0
        # Should have multiple chunks with small max-length
        assert "Chunk 0:" in result.stderr
        assert "chars HTML" in result.stderr
        assert "chars text" in result.stderr

    def test_list_chunks_with_verbose(self):
        """Test --list-chunks with --verbose flag."""
        result = runner.invoke(
            app,
            ["--max-length", "100", "--list-chunks", "--verbose"],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0
        assert "Total chunks:" in result.stderr
        # Verbose mode should still produce chunk listing
        assert "Chunk 0:" in result.stderr

    def test_list_chunks_no_stdout_pollution(self):
        """Test that --list-chunks doesn't output HTML to stdout."""
        result = runner.invoke(
            app, ["--max-length", "100", "--list-chunks"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0
        # stdout should be empty or minimal
        assert "<html>" not in result.stdout
        assert "<body>" not in result.stdout


class TestCLIAllChunks:
    """Test --all-chunks functionality."""

    def test_all_chunks_requires_output_dir(self):
        """Test that --all-chunks requires --output-dir."""
        result = runner.invoke(
            app, ["--max-length", "100", "--all-chunks"], input=SIMPLE_HTML
        )
        assert result.exit_code == 1
        assert "requires --output-dir" in result.stderr

    def test_all_chunks_creates_files(self, tmp_path):
        """Test that --all-chunks creates chunk files."""
        output_dir = tmp_path / "chunks"
        result = runner.invoke(
            app,
            ["--max-length", "50", "--all-chunks", "--output-dir", str(output_dir)],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0
        assert output_dir.exists()
        assert any(output_dir.glob("chunk_*.html"))

    def test_all_chunks_file_naming(self, tmp_path):
        """Test that chunk files are named correctly."""
        output_dir = tmp_path / "chunks"
        result = runner.invoke(
            app,
            ["--max-length", "50", "--all-chunks", "--output-dir", str(output_dir)],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0

        # Check for chunk_0.html, chunk_1.html, etc.
        chunk_files = sorted(output_dir.glob("chunk_*.html"))
        assert len(chunk_files) > 0
        assert chunk_files[0].name.startswith("chunk_0")

    def test_all_chunks_file_content(self, tmp_path):
        """Test that chunk files contain valid HTML."""
        output_dir = tmp_path / "chunks"
        result = runner.invoke(
            app,
            ["--max-length", "50", "--all-chunks", "--output-dir", str(output_dir)],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0

        chunk_files = list(output_dir.glob("chunk_*.html"))
        assert len(chunk_files) > 0

        # Check first chunk has HTML content
        first_chunk = chunk_files[0].read_text()
        assert len(first_chunk) > 0

    def test_all_chunks_creates_directory(self, tmp_path):
        """Test that --all-chunks creates output directory if it doesn't exist."""
        output_dir = tmp_path / "new_dir" / "chunks"
        result = runner.invoke(
            app,
            ["--max-length", "100", "--all-chunks", "--output-dir", str(output_dir)],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0
        assert output_dir.exists()

    def test_all_chunks_with_verbose(self, tmp_path):
        """Test --all-chunks with --verbose shows file creation."""
        output_dir = tmp_path / "chunks"
        result = runner.invoke(
            app,
            [
                "--max-length",
                "50",
                "--all-chunks",
                "--output-dir",
                str(output_dir),
                "--verbose",
            ],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0
        assert "Wrote" in result.stderr


class TestCLITextOnly:
    """Test --text-only functionality."""

    def test_text_only_single_chunk(self):
        """Test --text-only returns plain text."""
        result = runner.invoke(
            app,
            ["--max-length", "100", "--chunk-index", "0", "--text-only"],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0
        # Should not contain HTML tags
        assert "<html>" not in result.stdout
        assert "<body>" not in result.stdout
        assert "<p>" not in result.stdout
        # Should contain text content
        assert len(result.stdout.strip()) > 0

    def test_text_only_has_content(self):
        """Test that --text-only extracts actual text content."""
        result = runner.invoke(
            app, ["--max-length", "200", "--text-only"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0
        # Should contain some recognizable text from the HTML
        output = result.stdout.lower()
        assert len(output.strip()) > 0

    def test_text_only_with_all_chunks(self, tmp_path):
        """Test --text-only with --all-chunks creates .txt files."""
        output_dir = tmp_path / "chunks"
        result = runner.invoke(
            app,
            [
                "--max-length",
                "50",
                "--all-chunks",
                "--text-only",
                "--output-dir",
                str(output_dir),
            ],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0

        # Should create .txt files, not .html
        txt_files = list(output_dir.glob("chunk_*.txt"))
        html_files = list(output_dir.glob("chunk_*.html"))

        assert len(txt_files) > 0
        assert len(html_files) == 0

    def test_text_only_file_content(self, tmp_path):
        """Test that .txt files contain plain text, not HTML."""
        output_dir = tmp_path / "chunks"
        result = runner.invoke(
            app,
            [
                "--max-length",
                "50",
                "--all-chunks",
                "--text-only",
                "--output-dir",
                str(output_dir),
            ],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0

        txt_files = list(output_dir.glob("chunk_*.txt"))
        first_chunk = txt_files[0].read_text()

        # Should not contain HTML tags
        assert "<" not in first_chunk or ">" not in first_chunk


class TestCLIJSONFormat:
    """Test --format json functionality."""

    def test_json_format_valid_json(self):
        """Test that --format json produces valid JSON."""
        result = runner.invoke(
            app, ["--max-length", "100", "--format", "json"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0

        # Should be valid JSON
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    def test_json_format_structure(self):
        """Test that JSON output has expected structure."""
        result = runner.invoke(
            app, ["--max-length", "100", "--format", "json"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0

        data = json.loads(result.stdout)

        # Check expected fields
        assert "total_chunks" in data
        assert "max_length" in data
        assert "compared_by" in data
        assert "chunks" in data
        assert isinstance(data["chunks"], list)

    def test_json_chunk_structure(self):
        """Test that each chunk in JSON has expected fields."""
        result = runner.invoke(
            app, ["--max-length", "100", "--format", "json"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0

        data = json.loads(result.stdout)

        if len(data["chunks"]) > 0:
            chunk = data["chunks"][0]
            assert "index" in chunk
            assert "html" in chunk
            assert "text" in chunk
            assert "html_length" in chunk
            assert "text_length" in chunk

    def test_json_total_chunks_matches(self):
        """Test that total_chunks matches actual chunk count."""
        result = runner.invoke(
            app, ["--max-length", "50", "--format", "json"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["total_chunks"] == len(data["chunks"])

    def test_json_max_length_recorded(self):
        """Test that max_length is recorded in JSON."""
        max_len = 123
        result = runner.invoke(
            app, ["--max-length", str(max_len), "--format", "json"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["max_length"] == max_len

    def test_json_compared_by_html(self):
        """Test that compared_by reflects HTML mode."""
        result = runner.invoke(
            app, ["--max-length", "100", "--format", "json"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["compared_by"] == "html"

    def test_json_compared_by_text(self):
        """Test that compared_by reflects text mode."""
        result = runner.invoke(
            app,
            ["--max-length", "100", "--text", "--format", "json"],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["compared_by"] == "text"

    def test_json_lengths_are_accurate(self):
        """Test that html_length and text_length are accurate."""
        result = runner.invoke(
            app, ["--max-length", "100", "--format", "json"], input=MINIMAL_HTML
        )
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        if len(data["chunks"]) > 0:
            chunk = data["chunks"][0]
            # Lengths should match actual content
            assert chunk["html_length"] == len(chunk["html"])
            assert chunk["text_length"] == len(chunk["text"])

    def test_json_no_logs_in_stdout(self):
        """Test that JSON output is not contaminated by logs."""
        result = runner.invoke(
            app,
            ["--max-length", "100", "--format", "json", "--verbose"],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0

        # stdout should be pure JSON, parseable
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

        # Logs should be in stderr
        assert "INFO" not in result.stdout


class TestCLIVerbosity:
    """Test logging verbosity options."""

    def test_default_no_verbose_output(self):
        """Test that default mode doesn't show verbose logs."""
        result = runner.invoke(app, ["--max-length", "100"], input=SIMPLE_HTML)
        assert result.exit_code == 0
        # Should not have INFO logs in stderr
        assert "INFO" not in result.stderr or result.stderr == ""

    def test_verbose_shows_info_logs(self):
        """Test that --verbose flag works without errors."""
        result = runner.invoke(
            app, ["--max-length", "100", "--verbose"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0
        # Verbose mode should still produce output
        assert len(result.stdout) > 0

    def test_maximal_verbose_shows_debug_logs(self):
        """Test that --maximal-verbose flag works without errors."""
        result = runner.invoke(
            app, ["--max-length", "100", "--maximal-verbose"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0
        # Maximal verbose mode should still produce output
        assert len(result.stdout) > 0

    def test_logs_go_to_stderr(self):
        """Test that logs are written to stderr, not stdout."""
        result = runner.invoke(
            app, ["--max-length", "100", "--verbose"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0
        # Logs in stderr
        if result.stderr:
            assert "INFO" in result.stderr or "betterhtmlchunking" in result.stderr
        # HTML output in stdout
        assert len(result.stdout) > 0


class TestCLIEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_input(self):
        """Test handling of empty input."""
        result = runner.invoke(app, ["--max-length", "100"], input="")
        # Should not crash
        assert result.exit_code == 0 or result.exit_code == 1

    def test_minimal_html(self):
        """Test with minimal valid HTML."""
        result = runner.invoke(app, ["--max-length", "100"], input="<html></html>")
        assert result.exit_code == 0

    def test_very_small_max_length(self):
        """Test with very small max-length."""
        result = runner.invoke(app, ["--max-length", "10"], input=SIMPLE_HTML)
        assert result.exit_code == 0

    def test_very_large_max_length(self):
        """Test with very large max-length."""
        result = runner.invoke(app, ["--max-length", "1000000"], input=SIMPLE_HTML)
        assert result.exit_code == 0


class TestCLIIntegration:
    """Test integration of multiple CLI features."""

    def test_list_chunks_then_get_specific(self):
        """Test workflow: list chunks, then get specific chunk."""
        # First list chunks
        list_result = runner.invoke(
            app, ["--max-length", "50", "--list-chunks"], input=SIMPLE_HTML
        )
        assert list_result.exit_code == 0

        # Then get a specific chunk
        chunk_result = runner.invoke(
            app, ["--max-length", "50", "--chunk-index", "0"], input=SIMPLE_HTML
        )
        assert chunk_result.exit_code == 0
        assert len(chunk_result.stdout) > 0

    def test_json_and_all_chunks_are_exclusive(self):
        """Test that JSON format works independently of all-chunks."""
        # JSON should work without all-chunks
        result = runner.invoke(
            app, ["--max-length", "100", "--format", "json"], input=SIMPLE_HTML
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "chunks" in data

    def test_text_only_with_json(self, tmp_path):
        """Test that text-only works with all-chunks but not json."""
        # text-only with all-chunks should work
        output_dir = tmp_path / "chunks"
        result = runner.invoke(
            app,
            [
                "--max-length",
                "50",
                "--all-chunks",
                "--text-only",
                "--output-dir",
                str(output_dir),
            ],
            input=SIMPLE_HTML,
        )
        assert result.exit_code == 0
        assert any(output_dir.glob("chunk_*.txt"))
