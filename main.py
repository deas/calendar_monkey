import sys
import os
import pytz
import datetime
import logging
from calendar_monkey.calendar import CalendarApi, create_cache
import click
import json

from calendar_monkey.config import load_config

# import time
# import atexit

log = logging.getLogger(__name__)


@click.group()
@click.option("--debug", default=False)
@click.option("--config-file", "-c", default="calendar_monkey.json", show_default=True)
@click.pass_context
def cli(ctx, debug, config_file):
    ctx.ensure_object(dict)

    ctx.obj["CONFIG"] = load_config(config_file)

    tz = pytz.timezone(ctx.obj["CONFIG"].timezone)

    ctx.obj["NOW"] = tz.localize(datetime.datetime.now())

    logging_level = logging.INFO

    if debug:
        logging_level = logging.DEBUG

    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@cli.command()
@click.option("--days-offset", default=0, show_default=True)
@click.option("--days", default=7, show_default=True)
@click.option("--events", default=1, show_default=True)
@click.option("--dry-run", default=False, show_default=True)
@click.pass_context
def cancel_entries(ctx, days_offset, days, events, dry_run):
    cfg = ctx.obj["CONFIG"]
    # date = ctx.obj['NOW'].replace(hour=0, minute=0, second=0, microsecond=0)

    cache = create_cache(cfg.graph.cache_path)
    calApi = CalendarApi(cfg.graph, cache, cfg.timezone)
    calApi.login()
    result = calApi.cancel(days_offset, days, events, dry_run)

    if not result:
        click.echo("cancel entries failed")
        sys.exit(1)
    click.echo("%s events canceled " % result)


if __name__ == "__main__":
    cli(obj={})
