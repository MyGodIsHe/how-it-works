def test(run):
    got = run('src', 'main')
    assert got == {
        'main -> m1.m2.f1',
    }
