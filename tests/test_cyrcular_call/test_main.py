def test(run):
    got = run('src', 'main')
    assert got == {
        'main -> main.f1',
        'main.f1 -> main.f2',
        'main.f2 -> main.f1',
        'main -> main.f3',
        'main.f3 -> main.f3',
    }
