class BaseWorker:
    async def run(self):
        pass


class Worker1(BaseWorker):
    async def run(self):
        while True:
            print(1 + 1)


class Worker2(BaseWorker):
    async def run(self):
        while True:
            print(2 + 2)
