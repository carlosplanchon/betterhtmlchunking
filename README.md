# betterhtmlchunking

![Banner](https://raw.githubusercontent.com/carlosplanchon/betterhtmlchunking/main/assets/banner.jpg)


A Python library for intelligently chunking HTML documents into structured, size-limited segments based on DOM tree analysis.

## Our Discord Server:
[https://discord.gg/2uVF5FZg](https://discord.gg/EgXeu9qnrR)

## Overview

This library processes HTML content to split it into semantically coherent chunks while respecting specified size constraints. It analyzes the DOM structure to identify optimal split points, preserving contextual information and document hierarchy.

### DeepWiki Docs: [https://deepwiki.com/carlosplanchon/betterhtmlchunking](https://deepwiki.com/carlosplanchon/betterhtmlchunking)

## Key Features

- Custom DOM tree representation. 
- Configurable chunk size limits (counting by text or HTML length).
- Intelligent region-of-interest detection.
- Dual output formats: HTML and plain text chunks.  
- Preservation of structure relationships.
- Customizable tag filtering.

## Installation

```bash
pip install betterhtmlchunking
```

### Dependencies
- Python 3.12+
- attrs
- treelib
- beautifulsoup4
- parsel-text
- lxml
- attrs-strict

## Usage

### Basic Example

```python
from betterhtmlchunking import DomRepresentation
from betterhtmlchunking.main import ReprLengthComparisionBy
from betterhtmlchunking.main import tag_list_to_filter_out

html_content = """
<html>
  <body>
    <div id="content">
      <h1>Document Title</h1>
      <p>First paragraph...</p>
      <p>Second paragraph...</p>
    </div>
  </body>
</html>
"""

# Create document representation with 20 character chunks.
dom_repr = DomRepresentation(
    MAX_NODE_REPR_LENGTH=20,
    website_code=html_content,
    repr_length_compared_by=ReprLengthComparisionBy.HTML_LENGTH
    # tag_list_to_filter_out=["/head", "/header", "..."]  # By default tag_list_to_filter_out is used.
)
dom_repr.start()

# Render HTML:
for idx in dom_repr.tree_regions_system.sorted_roi_by_pos_xpath:
    print("*" * 50)
    print(f"IDX: {idx}")
    roi_html_render: str =\
        dom_repr.render_system.get_roi_html_render_with_pos_xpath(
            roi_idx=idx
        )
    print(roi_html_render)


# Render text:
for idx in dom_repr.tree_regions_system.sorted_roi_by_pos_xpath:
    print("*" * 50)
    print(f"IDX: {idx}")
    roi_text_render: str =\
        dom_repr.render_system.get_roi_text_render_with_pos_xpath(
            roi_idx=idx
        )
    print(roi_text_render)

```

Render output (HTML):
```
**************************************************
IDX: 0
<h1>
 Document Title
</h1>

**************************************************
IDX: 1
<p>
 First paragraph...
</p>

**************************************************
IDX: 2
<p>
 Second paragraph...
</p>
```

Render output (text):
```
**************************************************
IDX: 0
Document Title

**************************************************
IDX: 1
First paragraph...

**************************************************
IDX: 2
Second paragraph...
```


## Configuration

### Key Parameters
- `MAX_NODE_REPR_LENGTH`: Maximum allowed length for each chunk (in characters)
- `repr_length_compared_by`: Length calculation method:
  - ReprLengthComparisionBy.HTML_LENGTH: HTML source length
  - ReprLengthComparisionBy.TEXT_LENGTH: Rendered text length
- `website_code`: Input HTML content

### Advanced Features
```python
# Access the DOM tree structure
tree = dom_repr.tree_representation.tree

# Get node metadata:
for node in tree.all_nodes():
    if node.data is not None:
        print(f"XPath: {node.identifier}")
        print(f"Text length: {node.data.text_length}")
        print(f"HTML length: {node.data.html_length}")

```

## How It Works

1. **DOM Parsing**  
   - Builds a tree representation of the HTML document.
   - Calculates metadata (text length, HTML length) for each node.

2. **Region Detection**  
   - Uses **Breadth First Search (BFS)** to traverse the DOM tree in a level-order fashion, ensuring that each node is processed systematically.
   - Combines nodes until the specified size limit is reached.
   - Preserves parent-child relationships to maintain contextual integrity.

3. **Chunk Generation**  
   - Creates HTML chunks with original markup.
   - Generates parallel text-only chunks.
   - Maintains chunk order based on document structure.

## Comparison to popular Chunking Techniques

The actual practice (Feb. 2025) is to use **plain-text** or **token-based** chunking strategies, primarily aimed at keeping prompts within certain token limits for large language models. This approach is ideal for quick semantic retrieval or QA tasks on *unstructured* text.

By contrast, **betterhtmlchunking** preserves the **HTML DOM structure**, calculating chunk boundaries based on each node’s text or HTML length. This approach is especially useful when you want to:
- Retain or leverage the **hierarchical relationships** in the HTML (e.g., headings, nested divs)  
- Filter out undesired tags or sections (like `<script>` or `<style>`)  
- Pinpoint exactly where each chunk originated in the document (via positional XPaths)

You can even combine the two techniques if you need both **structured extraction** (via betterhtmlchunking) and **LLM-friendly text chunking** (via LangChain) for advanced tasks such as summarization, semantic search, or large-scale QA pipelines.

## CLI

The package ships with a command line interface built with [Typer](https://typer.tiangolo.com/). You can pipe HTML to the tool and work with chunks in multiple ways.

### Basic Usage - Single Chunk

Get a specific chunk as HTML:

```bash
cat input.html | betterhtmlchunking --max-length 32768 --chunk-index 0 > chunk.html
```

By default the command reads from `stdin`, processes chunks up to a maximum length of 32,768 characters, and prints the HTML corresponding to chunk index `0` to `stdout`.

### List All Chunks

See how many chunks are created and their sizes without processing the full content:

```bash
cat input.html | betterhtmlchunking --max-length 32768 --list-chunks
```

Output:
```
Total chunks: 5
Chunk 0: 28543 chars HTML, 12834 chars text
Chunk 1: 31245 chars HTML, 15234 chars text
Chunk 2: 19823 chars HTML, 9234 chars text
...
```

### Save All Chunks

Extract all chunks to separate files:

```bash
cat input.html | betterhtmlchunking --max-length 32768 --all-chunks --output-dir ./chunks
```

This creates `chunk_0.html`, `chunk_1.html`, etc. in the specified directory.

### Text-Only Output

Get plain text content without HTML markup:

```bash
# Single chunk as text
cat input.html | betterhtmlchunking --max-length 32768 --chunk-index 0 --text-only > chunk.txt

# All chunks as text files
cat input.html | betterhtmlchunking --max-length 32768 --all-chunks --text-only --output-dir ./chunks
```

This creates `chunk_0.txt`, `chunk_1.txt`, etc. with plain text content.

### JSON Output

Get structured JSON output with all chunks and metadata:

```bash
cat input.html | betterhtmlchunking --max-length 32768 --format json > output.json
```

Output format:
```json
{
  "total_chunks": 5,
  "max_length": 32768,
  "compared_by": "html",
  "chunks": [
    {
      "index": 0,
      "html": "<h1>...</h1>",
      "text": "...",
      "html_length": 28543,
      "text_length": 12834
    },
    ...
  ]
}
```

This is useful for programmatic processing. You can pipe the output to tools like `jq` or process it with scripts:

```bash
# Extract only text from all chunks
cat input.html | betterhtmlchunking --format json | jq -r '.chunks[].text'

# Get chunk count
cat input.html | betterhtmlchunking --format json | jq '.total_chunks'

# Filter chunks by size
cat input.html | betterhtmlchunking --format json | jq '.chunks[] | select(.text_length > 1000)'
```

### Verbose Mode

Enable progress logging with `--verbose`. Logs are written to `stderr` so they don't interfere with chunk output:

```bash
cat input.html | betterhtmlchunking --max-length 32768 --all-chunks --output-dir ./chunks --verbose
```

### Maximal Verbose Mode

For detailed inspection of the DOM, nodes, ROIs, and chunk lengths, use `--maximal-verbose`. This logs:

* Total DOM nodes and their HTML/text lengths
* Each ROI (region of interest) with constituent node XPaths and lengths
* Final chunk HTML and text sizes

```bash
cat input.html | betterhtmlchunking --max-length 32768 --chunk-index 0 --maximal-verbose > chunk.html 2> logs.txt
```

* `chunk.html` contains the selected chunk HTML.
* `logs.txt` captures all detailed logging information.

This mode is useful for debugging, testing, or analyzing how the document is split into chunks.

### CLI Options Summary

| Option | Short | Description |
|--------|-------|-------------|
| `--max-length` | `-l` | Maximum length for each chunk (default: 32768) |
| `--chunk-index` | `-c` | Index of specific chunk to output (default: 0) |
| `--list-chunks` | | List all chunks with their sizes |
| `--all-chunks` | | Output all chunks (requires `--output-dir`) |
| `--output-dir` | `-o` | Directory to save chunks when using `--all-chunks` |
| `--text-only` | | Output plain text instead of HTML |
| `--format` | `-f` | Output format: `json` for structured JSON output |
| `--text` | | Compare length using text instead of HTML |
| `--verbose` | `-v` | Enable progress logging |
| `--maximal-verbose` | | Enable detailed debug logging |

---

## License

MIT License

## Contributing
Feel free to open issues or submit pull requests if you have suggestions or improvements.
