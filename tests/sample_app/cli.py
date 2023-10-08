import asyncio

import click
import uvicorn

from sample_app import web, workers


@click.command()
def cli():
    uvicorn.run(web.app)


@click.command()
def worker():
    w = workers.Worker1()
    w.run()
    asyncio.run(workers.Worker2().run())


if __name__ == '__main__':
    cli()
    worker()
