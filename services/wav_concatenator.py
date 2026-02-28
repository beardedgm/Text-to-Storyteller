import wave
import struct
import io


class WavConcatenator:
    def concatenate(self, wav_segments: list) -> bytes:
        """Concatenate multiple WAV byte sequences into a single WAV file.

        Builds the WAV header manually with pre-computed sizes rather than
        relying on the wave module's deferred header-patching, which can
        produce malformed RIFF size fields on some platforms.
        """
        if not wav_segments:
            raise ValueError("No WAV segments to concatenate")

        all_pcm_data = []
        params = None

        for i, segment_bytes in enumerate(wav_segments):
            with wave.open(io.BytesIO(segment_bytes), 'rb') as reader:
                seg_params = reader.getparams()

                if params is None:
                    params = seg_params
                elif (seg_params.nchannels != params.nchannels or
                      seg_params.sampwidth != params.sampwidth or
                      seg_params.framerate != params.framerate):
                    raise ValueError(
                        f"Audio parameter mismatch in segment {i}: expected "
                        f"{params.nchannels}ch/{params.sampwidth}B/"
                        f"{params.framerate}Hz, got "
                        f"{seg_params.nchannels}ch/{seg_params.sampwidth}B/"
                        f"{seg_params.framerate}Hz"
                    )

                pcm_data = reader.readframes(reader.getnframes())
                if not pcm_data:
                    raise ValueError(f"Segment {i} contains no audio data")
                all_pcm_data.append(pcm_data)

        total_pcm_bytes = sum(len(d) for d in all_pcm_data)
        if total_pcm_bytes == 0:
            raise ValueError("Concatenated audio contains no data")

        # Build a canonical PCM WAV file from scratch.
        # Header layout (44 bytes):
        #   Offset  Field               Size  Description
        #   0       "RIFF"              4     Chunk ID
        #   4       <file_size - 8>     4     Chunk size (everything after this field)
        #   8       "WAVE"              4     Format
        #   12      "fmt "              4     Subchunk1 ID
        #   16      16                  4     Subchunk1 size (16 for PCM)
        #   20      1                   2     Audio format (1 = PCM)
        #   22      nchannels           2     Number of channels
        #   24      framerate           4     Sample rate
        #   28      byte_rate           4     framerate * nchannels * sampwidth
        #   32      block_align         2     nchannels * sampwidth
        #   34      bits_per_sample     2     sampwidth * 8
        #   36      "data"              4     Subchunk2 ID
        #   40      total_pcm_bytes     4     Subchunk2 size
        #   44      <PCM data>          N     Raw audio samples

        byte_rate = params.framerate * params.nchannels * params.sampwidth
        block_align = params.nchannels * params.sampwidth

        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + total_pcm_bytes,       # RIFF chunk size
            b'WAVE',
            b'fmt ',
            16,                         # fmt chunk size (PCM)
            1,                          # audio format (PCM)
            params.nchannels,
            params.framerate,
            byte_rate,
            block_align,
            params.sampwidth * 8,       # bits per sample
            b'data',
            total_pcm_bytes,            # data chunk size
        )

        output = io.BytesIO()
        output.write(header)
        for pcm in all_pcm_data:
            output.write(pcm)

        output.seek(0)
        return output.read()
