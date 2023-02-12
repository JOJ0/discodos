import click


@click.command(name='stats')
@click.pass_obj
def stats_cmd(helper):
    """
    Displays statistics about the collection.

    Besides showing stats like the size of the collection (on Discogs vs. in
    the DiscoBASE) also counts on existing mixes, how many tracks they contain
    and which additional metadata is present, are availalbe.
    """
    click.echo(f'Hello')
