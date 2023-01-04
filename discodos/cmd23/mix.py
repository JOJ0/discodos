import click


@click.command(name='mix')
@click.argument('name', nargs=1)
def mix_cmd(name):
    """
    Simple command that says hello
    """
    click.echo(f'Hello {name}')
