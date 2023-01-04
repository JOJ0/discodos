import click


@click.command(name='search')
@click.argument('name', nargs=1)
def search_cmd(name):
    """
    Simple command that says hello
    """
    click.echo(f'Hello {name}')
