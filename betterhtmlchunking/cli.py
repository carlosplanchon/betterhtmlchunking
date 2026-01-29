#!/usr/bin/env python3

import sys
import json
import typer
import logging
from pathlib import Path
from .main import DomRepresentation, ReprLengthComparisionBy
from .logging_config import setup_root_logger, set_log_level, get_logger

app = typer.Typer(help="Chunk HTML documents from the command line")

# Setup root logger with default WARNING level
setup_root_logger(level=logging.WARNING)
logger = get_logger("cli")

@app.command()
def chunk(
    max_length: int = typer.Option(
        32768,
        "--max-length",
        "-l",
        help="Maximum length for a region of interest",
    ),
    chunk_index: int = typer.Option(
        None,
        "--chunk-index",
        "-c",
        help="Index of the chunk to output (default: 0 if not using --all-chunks or --list-chunks)",
    ),
    by_text: bool = typer.Option(
        False,
        "--text",
        help="Compare length using text instead of HTML",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging output",
    ),
    maximal_verbose: bool = typer.Option(
        False, "--maximal-verbose", help="Enable maximal verbose logging"
    ),
    list_chunks: bool = typer.Option(
        False,
        "--list-chunks",
        help="List information about all chunks without outputting content",
    ),
    all_chunks: bool = typer.Option(
        False,
        "--all-chunks",
        help="Output all chunks (requires --output-dir)",
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory to save chunks when using --all-chunks",
    ),
    text_only: bool = typer.Option(
        False,
        "--text-only",
        help="Output text content only (no HTML markup)",
    ),
    format: str = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: 'json' for structured JSON output",
    ),
):
    """Read HTML from stdin and output the selected chunk as HTML."""

    # Adjust logger level based on verbosity
    if maximal_verbose:
        set_log_level(logging.DEBUG)
    elif verbose:
        set_log_level(logging.INFO)
    else:
        set_log_level(logging.WARNING)

    html_input = sys.stdin.read()
    compare = (
        ReprLengthComparisionBy.TEXT_LENGTH
        if by_text
        else ReprLengthComparisionBy.HTML_LENGTH
    )

    dom = DomRepresentation(
        MAX_NODE_REPR_LENGTH=max_length,
        website_code=html_input,
        repr_length_compared_by=compare,
    )
    dom.start(verbose=verbose, maximal_verbose=maximal_verbose)

    # Handle --format json mode
    if format and format.lower() == "json":
        chunks_data = []
        for idx in sorted(dom.render_system.html_render_roi.keys()):
            html_content = dom.render_system.html_render_roi[idx]
            text_content = dom.render_system.text_render_roi[idx]
            chunks_data.append({
                "index": idx,
                "html": html_content,
                "text": text_content,
                "html_length": len(html_content),
                "text_length": len(text_content),
            })

        output = {
            "total_chunks": len(chunks_data),
            "max_length": max_length,
            "compared_by": "text" if by_text else "html",
            "chunks": chunks_data,
        }

        typer.echo(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Handle --list-chunks mode
    if list_chunks:
        total_chunks = len(dom.render_system.html_render_roi)
        typer.echo(f"Total chunks: {total_chunks}", err=True)
        for idx in sorted(dom.render_system.html_render_roi.keys()):
            html_len = len(dom.render_system.html_render_roi[idx])
            text_len = len(dom.render_system.text_render_roi[idx])
            typer.echo(
                f"Chunk {idx}: {html_len} chars HTML, {text_len} chars text",
                err=True
            )
        return

    # Handle --all-chunks mode
    if all_chunks:
        if output_dir is None:
            typer.echo(
                "Error: --all-chunks requires --output-dir to be specified",
                err=True
            )
            raise typer.Exit(code=1)

        output_dir.mkdir(parents=True, exist_ok=True)
        extension = "txt" if text_only else "html"

        for idx in sorted(dom.render_system.html_render_roi.keys()):
            content = (
                dom.render_system.text_render_roi[idx]
                if text_only
                else dom.render_system.html_render_roi[idx]
            )
            output_file = output_dir / f"chunk_{idx}.{extension}"
            output_file.write_text(content, encoding="utf-8")
            if verbose or maximal_verbose:
                typer.echo(f"Wrote {output_file}", err=True)

        typer.echo(
            f"Wrote {len(dom.render_system.html_render_roi)} chunks to {output_dir}",
            err=True
        )
        return

    # Handle single chunk output (default behavior)
    if chunk_index is None:
        chunk_index = 0

    if text_only:
        chunk_content = dom.render_system.text_render_roi.get(chunk_index, "")
    else:
        chunk_content = dom.render_system.html_render_roi.get(chunk_index, "")

    typer.echo(chunk_content)


if __name__ == "__main__":
    app()
