import click


@click.command(name='stats')
@click.argument('name', nargs=1)
def stats_cmd(name):
    """
    Simple command that says hello
    """
    click.echo(f'Hello {name}')
