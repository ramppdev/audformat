import audformat
import audformat.testing


def test_with_data(tmpdir):

    db = audformat.testing.create_db(minimal=False)

    # compare with self

    assert db == db
    assert db['files'] == db['files']
    assert db['files']['string'] == db['files']['string']
    assert db['files']['string'] != db['files']['int']  # different columns

    # compare with db that has different data

    db2 = audformat.testing.create_db(minimal=False)

    assert db != db2
    assert str(db) == str(db2)  # same header
    assert db['files'] != db2['files']
    assert db['files']['string'] != db2['files']['string']
    assert db.schemes['string'] == db2.schemes['string']  # same schemes

    # compare with db that has same data

    db.save(tmpdir)
    db3 = audformat.Database.load(tmpdir)

    assert db == db3
    assert db['files'] == db3['files']
    assert db['files']['string'] == db3['files']['string']

    # compare with column that has no data

    c_no_data = audformat.Column(
        scheme_id=db['files']['string'].scheme_id,
        rater_id=db['files']['string'].rater_id,
        description=db['files']['string'].description,
        meta=db['files']['string'].meta.copy()
    )

    assert str(db['files']['string']) == str(c_no_data)
    assert db['files']['string'] != c_no_data


def test_without_data(tmpdir):

    db = audformat.testing.create_db(minimal=True)

    # compare with self

    assert db == db

    # compare with db that has different header

    db2 = audformat.testing.create_db(minimal=True)
    db.meta['new'] = 'key'

    assert db != db2

    # compare with db that has same header

    db.save(tmpdir)
    db3 = audformat.Database.load(tmpdir)

    assert db == db3

    # compare two columns without data

    c1 = audformat.Column(description='c1')
    c2 = audformat.Column(description='c2')

    assert c1 != c2
