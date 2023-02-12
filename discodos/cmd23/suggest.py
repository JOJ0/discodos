import click


@click.command(name='suggest')
@click.argument('suggest_search', nargs=1, metavar='SEARCH_TERMS', default=0)
@click.option(
    "-b", "--bpm", 'suggest_bpm', type=int, metavar="BPM",
    help='''suggests tracks based on BPM value, within a
    pitch-range of +/-6 percent.''')
@click.option(
    "-k", "--key",'suggest_key', type=str, metavar="KEY",
    help='suggests tracks based on musical key.')
@click.pass_obj
def suggest_cmd(helper, suggest_search, suggest_bpm, suggest_key):
    """
    Suggests tracks based on what you've played before, views tracks
    within a BPM range or sharing a musical key.
    """
    click.echo(f'Hello {suggest_search}')
