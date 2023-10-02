import asyncio

import click
import uvicorn

from sample_app import web, workers


@click.command()
def cli():
    uvicorn.run(web.app)


@click.command()
def worker():
    asyncio.run(workers.worker())


if __name__ == '__main__':
    cli()
