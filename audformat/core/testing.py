import os
import random
from typing import (
    Union,
    Sequence,
    Callable,
    Dict,
    Tuple,
    Optional,
)

import numpy as np
import pandas as pd

import audeer
import audiofile as af

from audformat.core import define
from audformat.core.database import Database
from audformat.core.index import (
    filewise_index,
    segmented_index,
)
from audformat.core.media import Media
from audformat.core.rater import Rater
from audformat.core.scheme import Scheme
from audformat.core.split import Split
from audformat.core.table import Table
from audformat.core.column import Column


def add_table(
        db: Database,
        table_id: str,
        table_type: define.IndexType,
        *,
        columns: Union[
            str,
            Sequence[str],
            Dict[str, Union[
                str, Tuple[Optional[str], Optional[str]]
            ]],
        ] = None,
        num_files: Union[int, Sequence[int]] = 5,
        num_segments_per_file: int = 5,
        file_duration: Union[str, pd.Timedelta] = '5s',
        file_root: str = 'audio',
        p_none: float = None,
        split_id: str = None,
        media_id: str = None,
) -> Table:
    r"""Adds a table with random values.

    By default adds one column for every scheme in the database.
    To create a specific set of columns use ``columns``.
    If a ``media_id`` is passed, the file format will be
    determined from there. Otherwise WAV is used.

    Args:
        db: the database
        table_id: id of table that will be created
        table_type: the table type
        columns: a list of scheme_ids or a dictionary with column names as
            keys and tuples of ``(scheme_id, rater_id)`` as values. ``None``
            values are allowed
        num_files: by default files are named ``'001'``, ``'002'``, etc. up
            the number of files. For a different ordering a sequence of
            integers can be passed
        num_segments_per_file: number of segments per file (only applies to
            to segmented table)
        file_duration: the file duration
        file_root: file sub directory
        p_none: probability to draw invalid values
        split_id: optional split id
        media_id: optional media id

    """
    if isinstance(file_duration, str):
        file_duration = pd.Timedelta(file_duration)

    if columns is None:
        columns = columns or {s: (s, None) for s in list(db.schemes)}
    elif isinstance(columns, str):
        columns = {columns: (columns, None)}
    elif isinstance(columns, Sequence):
        columns = {s: (s, None) for s in columns}

    audio_format = 'wav'
    if media_id and db.media[media_id].format:
        audio_format = db.media[media_id].format

    if isinstance(num_files, int):
        files = [
            os.path.join(file_root, '{:03}.{}'.format(idx + 1, audio_format))
            for idx in range(num_files)
        ]
    else:
        files = [
            os.path.join(file_root, '{:03}.{}'.format(idx, audio_format))
            for idx in num_files
        ]
        num_files = len(num_files)

    if table_type == define.IndexType.FILEWISE:

        n_items = num_files
        db[table_id] = Table(
            filewise_index(files),
            split_id=split_id,
            media_id=media_id,
        )

    elif table_type == define.IndexType.SEGMENTED:

        n_items = num_files * num_segments_per_file
        starts = []
        ends = []
        new_files = []

        for file in files:

            times = [pd.to_timedelta(random.random() * file_duration, unit='s')
                     for _ in range(num_segments_per_file * 2)]
            times.sort()
            starts.extend(times[::2])
            ends.extend(times[1::2])
            new_files.extend([file] * num_segments_per_file)

        db[table_id] = Table(
            segmented_index(new_files, starts=starts, ends=ends),
            split_id=split_id,
            media_id=media_id,
        )

    for column_id, (scheme_id, rater_id) in columns.items():
        db[table_id][column_id] = Column(
            scheme_id=scheme_id,
            rater_id=rater_id,
        )
        if scheme_id is not None:
            db[table_id][column_id].set(
                db.schemes[scheme_id].draw(n_items, p_none=p_none)
            )

    return db[table_id]


def create_audio_files(
        db: Database,
        root: str,
        *,
        sample_generator: Callable[[float], float] = None,
        sampling_rate: int = 16000,
        channels: int = 1,
        file_duration: Union[str, pd.Timedelta] = '60s',
):
    r"""Create audio files for a database.

    By default empty files are created. A sample generator function can be
    passed to generate the samples. The function gets as input a time stamp
    and should create a sample in the amplitude range ``[-1..1]``.

    Args:
        db: the database
        root: root folder where the database is (or will be) stored
        sample_generator: sample generator
        sampling_rate: sampling rate in Hz
        channels: number of channels
        file_duration: file duration

    """
    file_duration = pd.to_timedelta(file_duration)
    root = audeer.safe_path(root)

    for file in db.files:
        path = os.path.join(root, file)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        n = int(file_duration.total_seconds() * sampling_rate)
        x = np.zeros((channels, n))
        if sample_generator:  # pragma: no cover
            ts = np.arange(n) / sampling_rate
            for c in range(channels):
                for idx, t in enumerate(ts):
                    x[c, idx] = sample_generator(t)
        af.write(path, x, sampling_rate)


def create_db(minimal: bool = False) -> Database:
    r"""Creates a database with content for unit tests.

    """
    ########
    # Head #
    ########

    db = Database(
        name='unittest',
        source='internal',
        usage=define.Usage.COMMERCIAL,
        languages=['de', 'English'],
    )

    if minimal:
        return db

    db.description = 'A database for unit testing.'
    db.meta['audformat'] = 'https://gitlab.audeering.com/tools/audformat'

    #########
    # Media #
    #########

    db.media['microphone'] = Media(
        format='wav', sampling_rate=16000, channels=1, bit_depth=16,
    )
    db.media['webcam'] = Media(
        format='avi', video_fps=25, video_resolution=[800, 600],
        video_depth=8, video_channels=3,
    )

    ##########
    # Raters #
    ##########

    db.raters['gold'] = Rater(
        description='Gold standard by taking the average ratings.')
    db.raters['machine'] = Rater(
        type=define.RaterType.MACHINE,
        description='Predictions made by the machine.',
        meta={'features': 'ComParE_2016', 'classifier': 'LibSVM'})

    ###########
    # Schemes #
    ###########

    db.schemes['string'] = Scheme()
    db.schemes['int'] = Scheme(
        dtype=define.DataType.INTEGER, minimum=0, maximum=100,
    )
    db.schemes['float'] = Scheme(
        dtype=define.DataType.FLOAT, minimum=-1.0, maximum=1.0,
    )
    db.schemes['time'] = Scheme(dtype=define.DataType.TIME)
    db.schemes['date'] = Scheme(dtype=define.DataType.DATE)
    db.schemes['label'] = Scheme(labels=['label1', 'label2', 'label3'])
    db.schemes['label_map_str'] = Scheme(
        labels={'label1': {'prop1': 1, 'prop2': 'a'},
                'label2': {'prop1': 2, 'prop2': 'b'},
                'label3': {'prop1': 3, 'prop2': 'c'}})
    db.schemes['label_map_int'] = Scheme(
        labels={1: {'prop1': 1, 'prop2': 'a'},
                2: {'prop1': 2, 'prop2': 'b'},
                3: {'prop1': 3, 'prop2': 'c'}})

    ##########
    # Splits #
    ##########

    db.splits['train'] = Split(type=define.SplitType.TRAIN)
    db.splits['dev'] = Split(type=define.SplitType.DEVELOP)
    db.splits['test'] = Split(type=define.SplitType.TEST)

    ##########
    # Tables #
    ##########

    add_table(db, 'files', define.IndexType.FILEWISE,
              columns={
                  scheme: (scheme, 'gold') for scheme in list(db.schemes)
              },
              num_files=100, p_none=0.25, split_id='train',
              media_id='microphone')
    db['files']['no_scheme'] = Column()
    db['files']['no_scheme'].set(db.schemes['string'].draw(
        100, p_none=0.25)
    )

    add_table(db, 'segments', define.IndexType.SEGMENTED,
              columns={
                  scheme: (scheme, 'gold') for scheme in list(db.schemes)
              },
              num_files=10, num_segments_per_file=10,
              file_duration='60s', p_none=0.25, split_id='dev',
              media_id='microphone')
    db['segments']['no_scheme'] = Column()
    db['segments']['no_scheme'].set(db.schemes['string'].draw(
        100, p_none=0.25)
    )

    return db
