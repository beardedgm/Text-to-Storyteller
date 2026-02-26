import re


class TextChunker:
    def __init__(self, max_bytes: int = 4800):
        self.max_bytes = max_bytes
        self.ssml_overhead = 200
        self.effective_max = max_bytes - self.ssml_overhead

    def chunk(self, text: str) -> list:
        """Split text into chunks that fit within the TTS byte limit.

        Splitting priority (highest to lowest preference):
        1. Section breaks ([SECTION_BREAK_N] markers)
        2. Paragraph boundaries (double newline)
        3. Sentence boundaries (. ! ? followed by space)
        4. Clause boundaries (, ; : followed by space)
        5. Word boundaries (space)
        """
        sections = re.split(r'(\[SECTION_BREAK_\d\])', text)

        chunks = []
        current_chunk = ''

        for section in sections:
            if not section:
                continue

            if self._byte_len(current_chunk + section) <= self.effective_max:
                current_chunk += section
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                if self._byte_len(section) > self.effective_max:
                    sub_chunks = self._split_large_section(section)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ''
                else:
                    current_chunk = section

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _split_large_section(self, text: str) -> list:
        """Split a section that exceeds byte limit at paragraph,
        then sentence, then clause, then word boundaries."""
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 1:
            return self._accumulate(paragraphs, separator='\n\n')

        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 1:
            return self._accumulate(sentences, separator=' ')

        clauses = re.split(r'(?<=[,;:])\s+', text)
        if len(clauses) > 1:
            return self._accumulate(clauses, separator=' ')

        words = text.split()
        return self._accumulate(words, separator=' ')

    def _accumulate(self, pieces: list, separator: str) -> list:
        """Greedily accumulate pieces into chunks under the byte limit."""
        chunks = []
        current = ''
        for piece in pieces:
            candidate = current + separator + piece if current else piece
            if self._byte_len(candidate) <= self.effective_max:
                current = candidate
            else:
                if current:
                    chunks.append(current.strip())
                current = piece
        if current:
            chunks.append(current.strip())
        return chunks

    @staticmethod
    def _byte_len(text: str) -> int:
        return len(text.encode('utf-8'))
