#!/usr/bin/env python3
"""
Yada Bible Word Search Tool
Generates an offline HTML report highlighting occurrences of a search term (direct, reversed, equidistant letter sequences) in the KJV Bible as words.

"""

# For alternate searches other than the default...
# python3 yada.py -t LOVE -i /path/to/kjv.txt -o search-love.html

import re
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Yada: Search for words in the KJV Bible and generate an HTML report."
    )
    parser.add_argument(
        '-t', '--term', default='CHRIST',
        help='Search term (default: CHRIST)'
    )
    parser.add_argument(
        '-i', '--input', default='kjv.txt',
        help='Path to the KJV text file (default: kjv.txt)'
    )
    parser.add_argument(
        '-o', '--output', default='report.html',
        help='Output HTML file (default: report.html)'
    )
    return parser.parse_args()


def load_bible(path):
    """
    Parse KJV text file assuming each line starts with:
      Book Chapter:Verse Text...
    Returns list of {'book','chapter','verse','text'}
    """
    verses = []
    pattern = re.compile(r'^([1-3]?\s*\w+)\s+(\d+):(\d+)\s+(.*)')
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = pattern.match(line)
            if m:
                verses.append({
                    'book': m.group(1),
                    'chapter': m.group(2),
                    'verse':   m.group(3),
                    'text':    m.group(4)
                })
    return verses


def escape_html(text):
    """Escape &, <, > in text."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def highlight_text(text, matches, css_class):
    """
    Wrap each match interval in <span class="..."> for highlighting.
    `matches` is a list of (start_index, length).
    """
    if not matches:
        return escape_html(text)
    parts = []
    last = 0
    for start, length in sorted(matches, key=lambda x: x[0]):
        parts.append(escape_html(text[last:start]))
        segment = escape_html(text[start:start+length])
        parts.append(f'<span class="{css_class}">{segment}</span>')
        last = start + length
    parts.append(escape_html(text[last:]))
    return ''.join(parts)


def find_direct(text, term):
    text_u = text.upper()
    term_u = term.upper()
    matches = []
    idx = text_u.find(term_u)
    while idx != -1:
        matches.append((idx, len(term_u)))
        idx = text_u.find(term_u, idx + len(term_u))
    return matches


def find_reversed(text, term):
    text_u = text.upper()
    rev = term.upper()[::-1]
    matches = []
    idx = text_u.find(rev)
    while idx != -1:
        matches.append((idx, len(rev)))
        idx = text_u.find(rev, idx + len(rev))
    return matches


def find_els(text, term, max_skip=50):
    """
    Equidistant letter sequences (ELS) on letters only, up to a given skip.
    Returns list of {'skip', 'positions', 'cleaned'}.
    `positions` refer to indices in the cleaned text.
    """
    letters = re.findall('[A-Za-z]', text)
    cleaned = ''.join(letters)
    cu = cleaned.upper()
    tu = term.upper()
    length = len(tu)
    results = []
    n = len(cu)
    for skip in range(1, max_skip + 1):
        for start in range(n):
            end = start + (length - 1) * skip
            if end >= n:
                break
            seq = ''.join(cu[start + i * skip] for i in range(length))
            if seq == tu:
                positions = [start + i * skip for i in range(length)]
                results.append({'skip': skip, 'positions': positions, 'cleaned': cleaned})
    return results


def generate_html(verses, term):
    # Count occurrences for navigation
    direct_count = sum(len(find_direct(v['text'], term)) for v in verses)
    reverse_count = sum(len(find_reversed(v['text'], term)) for v in verses)
    els_count = sum(len(find_els(v['text'], term)) for v in verses)

    html = []
    html.append('<!DOCTYPE html>')
    html.append('<html lang="en">')
    html.append('<head>')
    html.append('  <meta charset="UTF-8">')
    html.append(f'  <title>Yada Bible Word Search Report for "{term}"</title>')
    html.append('  <style>')
    html.append('    body { font-family: sans-serif; white-space: pre-wrap; }')
    html.append('    .highlight-direct { background: yellow; }')
    html.append('    .highlight-reverse { background: cyan; }')
    html.append('    .highlight-els { background: magenta; }')
    html.append('    nav { margin-bottom: 1em; }')
    html.append('    nav a { margin-right: 1em; text-decoration: none; }')
    html.append('    h1, h2, h3 { margin-top: 1em; }')
    html.append('  </style>')
    html.append('</head>')
    html.append('<body>')
    html.append(f'<h1>Search Term: {term}</h1>')
    html.append('<nav>')
    html.append(f'<a href="#conventional">Conventional Matches ({direct_count})</a> | '
                 f'<a href="#reversed">Reversed Matches ({reverse_count})</a> | '
                 f'<a href="#els">Equidistant Matches ({els_count})</a>')
    html.append('</nav>')

    # Conventional matches
    html.append('<h2 id="conventional">Conventional Matches</h2>')
    for v in verses:
        dm = find_direct(v['text'], term)
        if dm:
            loc = f"{v['book']} {v['chapter']}:{v['verse']}"
            html.append(f'<h3>{loc}</h3>')
            html.append(f'<p>{highlight_text(v['text'], dm, 'highlight-direct')}</p>')

    # Reversed matches
    html.append('<h2 id="reversed">Reversed Matches</h2>')
    for v in verses:
        rm = find_reversed(v['text'], term)
        if rm:
            loc = f"{v['book']} {v['chapter']}:{v['verse']}"
            html.append(f'<h3>{loc}</h3>')
            html.append(f'<p>{highlight_text(v['text'], rm, 'highlight-reverse')}</p>')

    # ELS matches
    html.append('<h2 id="els">Equidistant Letter Sequences (ELS)</h2>')
    for v in verses:
        els = find_els(v['text'], term)
        if els:
            loc_base = f"{v['book']} {v['chapter']}:{v['verse']}"
            for m in els:
                skip = m['skip']
                pos = m['positions']
                cleaned = m['cleaned']
                highlights = [(p, 1) for p in pos]
                subtitle = f"{loc_base} (skip={skip})"
                html.append(f'<h3>{subtitle}</h3>')
                html.append(f'<p>{highlight_text(cleaned, highlights, 'highlight-els')}</p>')

    html.append('</body>')
    html.append('</html>')
    return '\n'.join(html)


def main():
    args = parse_args()
    verses = load_bible(args.input)
    report = generate_html(verses, args.term)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Report generated: {args.output}")

if __name__ == '__main__':
    main()
