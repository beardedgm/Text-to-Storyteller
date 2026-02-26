import mistune
import re


class TextRenderer(mistune.BaseRenderer):
    """Custom renderer that converts Markdown AST to
    narrator-friendly plain text with structural markers."""

    NAME = 'text'

    def _children(self, token, state):
        """Render child tokens to text."""
        children = token.get('children')
        if children:
            return self.render_tokens(children, state)
        return token.get('raw', token.get('text', ''))

    def text(self, token, state):
        return token.get('raw', token.get('children', ''))

    def heading(self, token, state):
        children = self._children(token, state)
        level = token['attrs']['level']
        return f'\n\n[SECTION_BREAK_{level}]{children}\n\n'

    def paragraph(self, token, state):
        children = self._children(token, state)
        return f'{children}\n\n'

    def list(self, token, state):
        return self._children(token, state)

    def list_item(self, token, state):
        children = self._children(token, state)
        return f'{children}\n'

    def emphasis(self, token, state):
        return self._children(token, state)

    def strong(self, token, state):
        return self._children(token, state)

    def codespan(self, token, state):
        return token.get('raw', '')

    def block_code(self, token, state):
        return f'\n{token.get("raw", "")}\n\n'

    def thematic_break(self, token, state):
        return '\n[SECTION_BREAK_1]\n\n'

    def link(self, token, state):
        return self._children(token, state)

    def image(self, token, state):
        alt = token.get('attrs', {}).get('alt', '')
        return f'(Image: {alt})' if alt else ''

    def block_html(self, token, state):
        return ''

    def inline_html(self, token, state):
        return ''

    def softbreak(self, token, state):
        return '\n'

    def linebreak(self, token, state):
        return '\n'

    def blank_line(self, token, state):
        return '\n'

    def block_quote(self, token, state):
        children = self._children(token, state)
        return f'{children}\n\n'

    def table(self, token, state):
        return self._children(token, state)

    def table_head(self, token, state):
        return self._children(token, state)

    def table_body(self, token, state):
        return self._children(token, state)

    def table_row(self, token, state):
        cells = self._children(token, state)
        return f'{cells}\n'

    def table_cell(self, token, state):
        children = self._children(token, state)
        is_head = token.get('attrs', {}).get('is_head', False)
        if is_head:
            return f'{children}: '
        return f'{children}. '

    def strikethrough(self, token, state):
        return self._children(token, state)


class MarkdownProcessor:
    def __init__(self):
        self.renderer = TextRenderer()
        self.md = mistune.create_markdown(renderer=self.renderer)

    def process(self, markdown_text: str) -> str:
        """Convert markdown to narrator-friendly plain text."""
        text = self.md(markdown_text)
        # Clean up excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        return text
