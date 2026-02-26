import re
from html import escape


class SSMLBuilder:
    BREAK_DURATIONS = {
        '1': '1500ms',  # H1: chapter break
        '2': '1000ms',  # H2: major section
        '3': '700ms',   # H3: subsection
    }

    def build(self, text_chunk: str) -> str:
        """Convert a plain text chunk with structural markers into SSML."""
        ssml = escape(text_chunk)

        for level, duration in self.BREAK_DURATIONS.items():
            marker = escape(f'[SECTION_BREAK_{level}]')
            ssml = ssml.replace(
                marker,
                f'<break time="{duration}"/>'
            )

        # Paragraph breaks -> medium pause
        ssml = re.sub(r'\n\n+', '<break time="500ms"/>', ssml)

        # Single newlines -> short pause
        ssml = ssml.replace('\n', '<break time="250ms"/>')

        ssml = f'<speak>{ssml}</speak>'
        return ssml
