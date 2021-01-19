# cli.py
import os
import re
from logging import ERROR, INFO

import click
import pyperclip

from database_manager.models import SQLAlchemyManager
from log_manager.models import log_and_print
from settings import FILE_DB
from units_manager.models import UnitsComposition


def validate_new_user(ctx, param, value):
    """
    Check new user name
    """
    if not re.match('^[A-Za-z][A-Za-z0-9_-]*$', value):
        log_and_print('The user name must consist of English letters, '
                      'numbers, and underscores. Start with a letter', level=ERROR)
        exit(-1)
    else:
        return value


def validate_user(ctx, param, value):
    """
    Check user exists
    """
    manager_obj = SQLAlchemyManager(FILE_DB, value)

    if not manager_obj.user_obj.check_user():
        log_and_print(f'User named "{value}" not exists', level=ERROR)
        exit(-1)
    elif 'PASSWORD' in ctx.obj.keys() \
            and not manager_obj.user_obj.check_user_password(ctx.obj['PASSWORD']):
        log_and_print(f'Incorrect password for user named "{value}"', level=ERROR)
        exit(-1)
    else:
        ctx.obj['USER'] = value
        return value


def validate_password(ctx, param, value):
    """
    Check password
    """
    if 'USER' not in ctx.obj.keys():
        ctx.obj['PASSWORD'] = value
        return value

    user = ctx.obj['USER']
    manager_obj = SQLAlchemyManager(FILE_DB, user)

    if not manager_obj.user_obj.check_user_password(value):
        log_and_print(f'Incorrect password for user named "{user}"', level=ERROR)
        exit(-1)
    else:
        return value


def msg_login_exist(login, name):
    log_and_print(f'login "{login}" with "{name}" name already exists', level=ERROR)


def msg_login_not_exist(login, name):
    log_and_print(f'login "{login}" with "{name}" name not exists', level=ERROR)


user_argument = click.option('--user', '-u', prompt="Username",
                             help="Provide your username",
                             callback=validate_user,
                             default=os.getlogin)
password_argument = click.option('--password', '-p', help="Provide your password",
                                 callback=validate_password,
                                 prompt=True, hide_input=True)


@click.group()
# @click.option('-n/-not-name', help='print or not name')
@click.option('-c/-not-category', help='print or not category')
@click.option('-u/-not-url', help='print or not url')
@click.pass_context
def cli(ctx, c, u):
    """
    pwdone is a multi-user, multi-platform command-line utility
    for storing and organizing passwords and another info for logins

    Samples:

    \b
    adding a new user:
    $ pwdone uadd
    or using options:
    $ pwdone uadd -u user-name

    \b
    adding a new record in passwords DB:
    $ pwdone add
    or using options:
    $ pwdone add -u user-name -l login-for-site -n record-name

    \b
    show all user records:
    $ pwdone show

    \b
    get the password of record to the clipboard:
    $ pwdone get

    \b
    full list of command options:
    $ pwdone [command] --help
    """
    ctx.obj = {
        'FLAGS': {
            'name': True,
            'category': c,
            'url': u
        }
    }


@cli.command()
@click.option('--user', '-u', prompt="Username",
              help="Provide your username",
              callback=validate_new_user,
              default=os.getlogin)
@click.option('--password', '-p', help="Provide your password",
              prompt=True, hide_input=True)
@click.option("--db", default=FILE_DB, required=False, hidden=True)
def uadd(user, password, db):
    """
    add user command
    """
    manager_obj = SQLAlchemyManager(db, user)

    if manager_obj.user_obj.check_user():
        log_and_print(f'User named "{user}" already exists', level=ERROR)
        exit(-1)
    else:
        manager_obj.user_obj.add_user(password)
        log_and_print(f'User named "{user}" created', level=INFO)


@cli.command()
@user_argument
@password_argument
@click.option('-nu', '--new-username', prompt="New username",
              callback=validate_new_user, help="Provide new username")
@click.option('-np', '--new-password',
              prompt="New password (Press 'Enter' for keep old password)",
              default='',
              help="Provide new password for user", hide_input=True)
@click.confirmation_option(prompt='Are you sure you want to update user data?')
@click.option("--db", default=FILE_DB, required=False, hidden=True)
def uupdate(user, password,
            new_username, new_password, db):
    """
    update username (and password) command
    """
    manager_obj = SQLAlchemyManager(db, user)

    new_password = None if new_password == '' else new_password
    if manager_obj.user_obj.check_user(new_username) and not new_password:
        log_and_print(f'User named "{new_username}" already exists '
                      f'and no new password is given', level=ERROR)
    else:
        manager_obj.user_obj.update_user(db, password, new_username, new_password)
        log_and_print(f'User "{user}" updated. New username is "{new_username}"',
                      level=INFO)


@cli.command()
@user_argument
@password_argument
@click.option("--db", default=FILE_DB, required=False, hidden=True)
def udelete(user, password, db):
    """
    delete user command
    """
    manager_obj = SQLAlchemyManager(db, user)

    manager_obj.user_obj.del_user()
    log_and_print(f'User named "{user}" deleted', level=INFO)


@cli.command()
@click.option("--db", default=FILE_DB, required=False, hidden=True)
def ushow(db):
    """
    show users command
    """
    manager_obj = SQLAlchemyManager(db)

    users = manager_obj.user_obj.all_users()
    for user in users:
        print(user)
    log_and_print(f'Show users command is done', print_need=False, level=INFO)


@cli.command()
@user_argument
@password_argument
@click.option('-c', "--category", help='"default" for default category, '
                                       'skip for all logins, optional',
              default=None, required=False)
@click.pass_context
@click.option("--db", default=FILE_DB, required=False, hidden=True)
def show(ctx, user, password, category, db):
    """
    show logins command
    """
    manager_obj = SQLAlchemyManager(db, user)

    logins = manager_obj.unit_obj.get_logins(category)
    units_composition_obj = UnitsComposition(logins)
    units_composition_obj.prepare_data()
    res_str = units_composition_obj.make_str_logins(ctx.obj['FLAGS'])
    print(res_str)
    log_and_print(f'Show logins command is done', print_need=False, level=INFO)


@cli.command()
@user_argument
@password_argument
@click.option('-l', "--login", prompt="Login", help="Provide login")
@click.option('-n', "--name", prompt="Name", help='name', default='default')
@click.option("--db", default=FILE_DB, required=False, hidden=True)
def get(user, password, login, name, db):
    """
    get password by login command
    """
    manager_obj = SQLAlchemyManager(db, user)

    if manager_obj.unit_obj.check_login(login, name):
        pyperclip.copy(manager_obj.unit_obj.get_password(user, password, login, name))
        log_and_print(f'Password is placed on the clipboard', level=INFO)
    else:
        msg_login_not_exist(login, name)
        exit(-1)


@cli.command()
@user_argument
@password_argument
@click.option('-l', "--login", prompt="Login", help="Provide login")
@click.option('-n', "--name", prompt="Name", help='name', default='default')
@click.option("--db", default=FILE_DB, required=False, hidden=True)
def delete(user, password, login, name, db):
    """
    delete login and password command
    """
    manager_obj = SQLAlchemyManager(db, user)

    if manager_obj.unit_obj.check_login(login, name):
        manager_obj.unit_obj.delete_unit(login, name)
        log_and_print(f'Login "{login}" deleted', level=INFO)
    else:
        msg_login_not_exist(login, name)
        exit(-1)


@cli.command()
@user_argument
@password_argument
@click.option('-l', "--login", prompt="Login", help="Provide login")
@click.option('-pl', '--password-for-login', prompt=True,
              help="Provide password for login", hide_input=True)
@click.option('-n', "--name", prompt="Name", help='name', default='default')
@click.option('-c', "--category", help='"default" or skip for default category, optional',
              default=None, required=False)
@click.option('-ur', "--url", help='url, optional', default=None, required=False)
@click.option("--db", default=FILE_DB, required=False, hidden=True)
def add(user, password, login, password_for_login, category, url, name, db):
    """
    add login and password command
    """
    manager_obj = SQLAlchemyManager(db, user)

    if manager_obj.unit_obj.check_login(login, name):
        msg_login_exist(login, name)
        exit(-1)
    else:
        category = 'default' if category is None else category
        manager_obj.unit_obj.add_unit(user, password, login, password_for_login, name, category, url)
        log_and_print(f'Login "{login}" added', level=INFO)


@cli.command()
@user_argument
@password_argument
@click.option('-l', "--login", prompt="Login", help="Provide login")
@click.option('-n', "--name", prompt="Name", help='name', default='default')
@click.option('-nl', "--new-login", help='new login, optional',
              default=None, required=False)
@click.option('-nn', "--new-name", help='"default" or skip for old name, optional',
              default=None, required=False)
@click.option('-pl', '--password-for-login',
              prompt="New password for login (Press 'Enter' for keep old password)",
              default='',
              help="Provide new password for login", hide_input=True)
@click.option('-nc', "--new-category", help='"default" or skip for old category, optional',
              default=None, required=False)
@click.option('-ur', "--url", help='url, optional', default=None, required=False)
@click.option("--db", default=FILE_DB, required=False, hidden=True)
def update(user, password, login, name,
           new_login, new_name, password_for_login, new_category, url, db):
    """Update unit"""

    manager_obj = SQLAlchemyManager(db, user)

    new_login = login if new_login is None else new_login
    new_name = name if new_name is None else new_name

    if manager_obj.unit_obj.check_login(login, name):
        if new_login != login or new_name != name:
            if manager_obj.unit_obj.check_login(new_login, new_name):
                msg_login_exist(new_login, new_name)
                exit(-1)
        password_for_login = None if password_for_login == '' else password_for_login
        manager_obj.unit_obj.update_unit(user, password, login, name,
                                         new_login, password_for_login, new_category, url, new_name)
        log_and_print(f'Login "{login}" updated', level=INFO)
    else:
        msg_login_not_exist(login, name)
        exit(-1)


if __name__ == '__main__':
    cli()
