import click
from flask.cli import with_appcontext
from .models import db

@click.command('init-db')
@with_appcontext
def init_db_command():
    """ایجاد پایگاه داده و جداول"""
    db.create_all()
    click.echo('پایگاه داده با موفقیت ایجاد شد.')

def init_app(app):
    """اضافه کردن دستورات CLI به برنامه"""
    app.cli.add_command(init_db_command)
