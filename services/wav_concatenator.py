import wave
import io


class WavConcatenator:
    def concatenate(self, wav_segments: list) -> bytes:
        """Concatenate multiple WAV byte sequences into a single WAV file."""
        if not wav_segments:
            raise ValueError("No WAV segments to concatenate")

        first_wav = wave.open(io.BytesIO(wav_segments[0]), 'rb')
        params = first_wav.getparams()

        all_frames = []

        for segment_bytes in wav_segments:
            wav_reader = wave.open(io.BytesIO(segment_bytes), 'rb')
            seg_params = wav_reader.getparams()

            if (seg_params.nchannels != params.nchannels or
                    seg_params.sampwidth != params.sampwidth or
                    seg_params.framerate != params.framerate):
                wav_reader.close()
                raise ValueError(
                    f"Audio parameter mismatch: expected "
                    f"{params.nchannels}ch/{params.sampwidth}B/{params.framerate}Hz, "
                    f"got {seg_params.nchannels}ch/{seg_params.sampwidth}B/"
                    f"{seg_params.framerate}Hz"
                )

            frames = wav_reader.readframes(wav_reader.getnframes())
            all_frames.append(frames)
            wav_reader.close()

        first_wav.close()

        output_buffer = io.BytesIO()
        wav_writer = wave.open(output_buffer, 'wb')
        wav_writer.setparams(params)

        for frames in all_frames:
            wav_writer.writeframesraw(frames)

        wav_writer.close()
        output_buffer.seek(0)
        return output_buffer.read()
