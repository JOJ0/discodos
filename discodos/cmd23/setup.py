import click


@click.command(name='setup')
@click.argument('name', nargs=1)
def setup_cmd(name):
    """
    Simple command that says hello
    """
    click.echo(f'Hello {name}')
