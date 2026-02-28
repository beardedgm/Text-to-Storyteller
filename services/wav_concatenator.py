import struct
import io


class WavConcatenator:
    """Concatenate WAV segments using raw byte manipulation.

    Bypasses Python's wave module entirely to preserve the exact format
    returned by Google Cloud TTS.  For single-segment jobs the original
    bytes are returned untouched.
    """

    @staticmethod
    def _find_chunk(data: bytes, chunk_id: bytes, start: int = 12) -> tuple:
        """Walk RIFF chunks and return (offset, size) of the requested chunk.

        `start` defaults to 12 — right after the RIFF header (4 bytes ID +
        4 bytes size + 4 bytes 'WAVE').
        """
        pos = start
        while pos + 8 <= len(data):
            cid = data[pos:pos + 4]
            csize = struct.unpack_from('<I', data, pos + 4)[0]
            if cid == chunk_id:
                return pos, csize
            # Advance to next chunk (word-aligned per RIFF spec)
            pos += 8 + csize + (csize % 2)
        return None, None

    def concatenate(self, wav_segments: list) -> bytes:
        """Concatenate WAV byte sequences into a single WAV file.

        Strategy
        --------
        1. Single segment → return the Google TTS bytes *unchanged*.
        2. Multiple segments → parse each segment's raw bytes to locate the
           'data' chunk, pull out the PCM audio, and reassemble a new WAV
           that keeps the first segment's header (fmt + any extra chunks)
           with updated RIFF and data sizes.

        This avoids the Python `wave` module, which can silently alter
        headers during its read/write round-trip.
        """
        if not wav_segments:
            raise ValueError("No WAV segments to concatenate")

        # Fast path: single segment — zero processing
        if len(wav_segments) == 1:
            return wav_segments[0]

        # ── Multi-segment concatenation ─────────────────────────────
        all_audio = []
        header_bytes = None       # everything up to (not including) audio data
        data_size_offset = None   # byte offset of the data-chunk size field

        for i, seg in enumerate(wav_segments):
            if len(seg) < 44:
                raise ValueError(
                    f"Segment {i} too small to be a WAV file ({len(seg)} bytes)"
                )
            if seg[:4] != b'RIFF' or seg[8:12] != b'WAVE':
                raise ValueError(
                    f"Segment {i} is not a valid WAV file "
                    f"(starts with {seg[:4]!r}...{seg[8:12]!r})"
                )

            data_pos, data_size = self._find_chunk(seg, b'data')
            if data_pos is None:
                raise ValueError(f"No 'data' chunk found in segment {i}")

            audio_start = data_pos + 8
            audio = seg[audio_start:audio_start + data_size]

            if not audio:
                raise ValueError(f"Segment {i} 'data' chunk is empty")

            all_audio.append(audio)

            # Keep the first segment's complete header (everything before
            # the audio samples).  This preserves 'fmt ', 'fact', 'LIST',
            # or any other chunks Google TTS includes.
            if header_bytes is None:
                header_bytes = bytearray(seg[:audio_start])
                data_size_offset = data_pos + 4

        total_audio_bytes = sum(len(a) for a in all_audio)
        if total_audio_bytes == 0:
            raise ValueError("All segments were empty after parsing")

        # Patch the two size fields in the header
        # RIFF chunk size (offset 4) = total_file_size - 8
        riff_size = (len(header_bytes) - 8) + total_audio_bytes
        struct.pack_into('<I', header_bytes, 4, riff_size)
        # data chunk size
        struct.pack_into('<I', header_bytes, data_size_offset, total_audio_bytes)

        out = io.BytesIO()
        out.write(header_bytes)
        for audio in all_audio:
            out.write(audio)
        out.seek(0)
        return out.read()
