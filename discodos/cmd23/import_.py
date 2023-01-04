import click


@click.command(name='import')
@click.argument('name', nargs=1)
def import_cmd(name):
    """
    Simple command that says hello
    """
    click.echo(f'Hello {name}')
