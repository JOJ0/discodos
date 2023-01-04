import click


@click.command(name='suggest')
@click.argument('name', nargs=1)
def suggest_cmd(name):
    """
    Simple command that says hello
    """
    click.echo(f'Hello {name}')
