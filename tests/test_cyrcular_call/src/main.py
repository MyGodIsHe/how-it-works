def f1():
    f2()


def f2():
    f1()


def f3():
    f3()


f1()
f3()
