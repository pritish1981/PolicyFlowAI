"""Section-aware Markdown chunking; overlap never crosses headings."""
import re
from dataclasses import dataclass
import tiktoken


@dataclass(frozen=True)
class SectionChunk:
    section_id: str
    section_title: str
    content: str
    token_count: int


_ENCODING = tiktoken.get_encoding("cl100k_base")


def chunk_markdown(markdown: str, target: int = 550, overlap: int = 75) -> list[SectionChunk]:
    """Split each heading section independently using tokenizer tokens."""
    if not 400 <= target <= 700 or not 50 <= overlap <= 100 or overlap >= target:
        raise ValueError("target must be 400-700 and overlap 50-100")
    sections: list[tuple[str, str, list[str]]] = []
    current_id = ""
    current_title = ""
    lines: list[str] = []
    for line in markdown.splitlines():
        match = re.match(r"^(#{2,6})\s+(.+?)\s*$", line)
        if match:
            if current_id:
                sections.append((current_id, current_title, lines))
            current_title = match.group(2)
            slug = re.sub(r"[^a-z0-9]+", "-", current_title.lower()).strip("-")
            current_id = slug
            lines = []
        elif current_id:
            lines.append(line)
    if current_id:
        sections.append((current_id, current_title, lines))
    if len({item[0] for item in sections}) != len(sections):
        raise ValueError("section headings must be unique")
    result: list[SectionChunk] = []
    for section_id, title, section_lines in sections:
        token_ids = _ENCODING.encode("\n".join(section_lines).strip())
        if not token_ids:
            continue
        start = 0
        while start < len(token_ids):
            part = token_ids[start:start + target]
            result.append(SectionChunk(section_id, title, _ENCODING.decode(part), len(part)))
            if start + target >= len(token_ids):
                break
            start += target - overlap
    return result
