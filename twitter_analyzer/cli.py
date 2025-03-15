import click
from flask.cli import with_appcontext
from .models import db

@click.command('init-db')
@with_appcontext
def init_db_command():
    """ایجاد پایگاه داده و جداول"""
    db.create_all()
    click.echo('پایگاه داده با موفقیت ایجاد شد.')

@click.command('drop-db')
@with_appcontext
def drop_db_command():
    """حذف تمام جداول پایگاه داده"""
    if click.confirm('آیا مطمئن هستید؟ تمام داده‌ها از بین خواهند رفت!'):
        db.drop_all()
        click.echo('تمام جداول پایگاه داده حذف شدند.')

def init_app(app):
    """اضافه کردن دستورات CLI به برنامه"""
    app.cli.add_command(init_db_command)
    app.cli.add_command(drop_db_command)


    