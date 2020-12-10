import typing

from audformat.core import define
from audformat.core.common import HeaderBase


class MediaInfo(HeaderBase):
    r"""Base class holding media information.

    Args:
        type: media type
        description: media description
        meta: additional meta fields

    Raises:
        BadValueError: if an invalid ``type`` is passed

    """
    def __init__(
            self,
            type: define.MediaType,
            *,
            description: str = None,
            meta: dict = None,
    ):
        super().__init__(description=description, meta=meta)
        define.MediaType.assert_has_value(type)
        self.type = type


class AudioInfo(MediaInfo):
    r"""Audio media information.

    Args:
        format: audio file format (e.g. ``wav`` or ``flac``)
        sampling_rate: sampling rate in Hz
        channels: number of channels
        bit_depth: bit depth
        description: media description
        meta: additional meta fields

    """
    def __init__(
            self,
            *,
            format: str = None,
            sampling_rate: int = None,
            channels: int = None,
            bit_depth: int = None,
            description: str = None,
            meta: dict = None,
    ):

        super().__init__(
            define.MediaType.AUDIO,
            description=description,
            meta=meta,
        )

        self.channels = channels
        r"""Number of channels"""
        self.format = format
        r"""File format"""
        self.bit_depth = bit_depth
        r"""Bit depth"""
        self.sampling_rate = sampling_rate
        r"""Sampling rate in Hz"""


class VideoInfo(MediaInfo):
    r"""Video media information.

    Args:
        format: video file format (e.g. ``avi`` or ``mp4``)
        frames_per_second: number of frames per seconds (fps)
        resolution: resolution in width x height in pixels (e.g. ``[800,
            600]``)
        channels: number of values per pixel (e.g. 3 in case of RGB)
        depth: number of bits per channel
        description: media description
        meta: additional meta fields

    """
    def __init__(
            self,
            *,
            format: str = None,
            frames_per_second: int = None,
            resolution: typing.Sequence[int] = None,
            channels: int = None,
            depth: int = None,
            description: str = None,
            meta: dict = None,
    ):
        super().__init__(
            define.MediaType.VIDEO,
            description=description,
            meta=meta,
        )

        self.format = format
        r"""File format"""
        self.frames_per_second = frames_per_second
        r"""Frames per second"""
        self.resolution = resolution
        r"""Image resolution"""
        self.channels = channels
        r"""Number of channels"""
        self.depth = depth
        r"""Bit depth"""
