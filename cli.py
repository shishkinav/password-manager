# cli.py
import click
import logging
import log_manager.config
from os import getlogin as os_getlogin
from re import match as re_match
from pyperclip import copy as pyperclip_copy
from db_manager import managers as db_sql


logger = logging.getLogger(__name__)


def validate_new_username(ctx, param, value):
    """
    Check new user name
    """
    if 'USER' in ctx.obj.keys() and value == '':
        return value

    if not re_match('^[A-Za-z][A-Za-z0-9_-]*$', value):
        logger.error('The user name must consist of English letters, '
                     'numbers, and underscores. Start with a letter.')
        exit(-1)
    else:
        return value


def validate_user(ctx, param, value):
    """
    Check user exists
    """
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(ctx.obj['prod_db']))
    if not user_proxy.check_obj(filters={"username": value}):
        logger.error(f'User named "{value}" not exists')
        exit(-1)
    elif 'PASSWORD' in ctx.obj.keys() \
            and not user_proxy.check_user_password(
                username=value,
                password=ctx.obj['PASSWORD']
            ):
        logger.error(f'Incorrect password for user named "{value}"')
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
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(ctx.obj['prod_db']))
    if not user_proxy.check_user_password(
                username=user,
                password=value
            ):
        logger.error(f'Incorrect password for user named "{user}"')
        exit(-1)
    else:
        return value


def msg_login_exist(login, name):
    logger.error(f'login "{login}" with "{name}" name already exists')


def msg_login_not_exist(login, name):
    logger.error(f'login "{login}" with "{name}" name not exists')


user_argument = click.option('--user', '-u', prompt="Username",
                             help="Provide your username",
                             callback=validate_user,
                             default=os_getlogin)
password_argument = click.option('--password', '-p', help="Provide your password",
                                 callback=validate_password,
                                 prompt=True, hide_input=True)


@click.group()
# @click.option('-n/-not-name', help='print or not name')
@click.option('-c/-not-category', help='print or not category')
@click.option('-u/-not-url', help='print or not url')
@click.option('-prod_db/-test_db', default=True, help='which DB to use')
@click.pass_context
def cli(ctx, c, u, prod_db):
    """
    saverpwd is a multi-user, multi-platform command-line utility
    for storing and organizing passwords and another info for logins

    Samples:

    \b
    adding a new user:
    $ saverpwd uadd
    or using options:
    $ saverpwd uadd -u user-name

    \b
    adding a new record in passwords DB:
    $ saverpwd add
    or using options:
    $ saverpwd add -u user-name -l login-for-site -n record-name

    \b
    show all user records:
    $ saverpwd show

    \b
    get the password of record to the clipboard:
    $ saverpwd get

    \b
    full list of command options:
    $ saverpwd [command] --help
    """
    ctx.obj = {
        'FLAGS': {
            'name': True,
            'category': c,
            'url': u
        },
        'prod_db': prod_db,
    }


@cli.command()
@click.option('--user', '-u', prompt="Username",
              help="Provide your username",
              callback=validate_new_username,
              default=os_getlogin)
@click.option('--password', '-p', help="Provide your password",
              prompt=True, hide_input=True)
@click.pass_context
def uadd(ctx, user, password):
    """
    add user command
    """
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(ctx.obj['prod_db']))
    if user_proxy.check_obj(filters={"username": user}):
        logger.error(f'User named "{user}" already exists')
        exit(-1)
    else:
        user_proxy.add_obj({
            "username": user,
            "password": password
        })
        logger.info(f'User named "{user}" created')


@cli.command()
@user_argument
@password_argument
@click.option('-nu', '--new-username',
              prompt="New username (Press 'Enter' for keep old username)",
              default='', callback=validate_new_username, help="Provide new username")
@click.option('-np', '--new-password',
              prompt="New password (Press 'Enter' for keep old password)",
              default='', help="Provide new password for user", hide_input=True)
@click.confirmation_option(prompt='Are you sure you want to update user data?')
@click.pass_context
def uupdate(ctx, user, password,
            new_username, new_password):
    """
    update username (and password) command
    """
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(ctx.obj['prod_db']))
    if new_username != '' and new_password == '' \
            and user_proxy.check_obj(filters={"username": new_username}):
        logger.error(f'User named "{new_username}" already exists '
                     f'and no new password is given')
    else:
        data = {}
        if new_username != '':
            data["username"] = new_username
        if new_password != '':
            data["password"] = new_password
        if data == {}:
            logger.info(f'User not updated - nothing for update')
        else:
            data["current_password"] = password
            user_proxy.update_obj(filters={"username": user}, data=data)
            logger.info(f'User "{user}" updated')
            if new_username != '':
                logger.info(f'New username is "{new_username}"')


@cli.command()
@user_argument
@password_argument
@click.confirmation_option(prompt='Are you sure you want to delete all user data?')
@click.pass_context
def udelete(ctx, user, password):
    """
    delete user command
    """
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(ctx.obj['prod_db']))
    user_proxy.delete_obj(filters={"username": user})
    logger.info(f'User named "{user}" deleted')


@cli.command()
@click.pass_context
def ushow(ctx):
    """
    show users command
    """
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(ctx.obj['prod_db']))
    users = user_proxy.manager.get_objects(filters={})
    for user in users:
        print(user.username)
    logger.info(f'Show users command is done')


@cli.command()
@user_argument
@password_argument
@click.option('-c', "--category", help='"default" for default category, '
                                       'skip for all logins, optional',
              default=None, required=False)
@click.pass_context
def show(ctx, user, password, category):
    """
    show logins command
    """
    # manager_obj = SQLAlchemyManager(ctx.obj['DB'], user)
    # logins = manager_obj.unit_obj.get_logins(category)
    # units_composition_obj = UnitsComposition(logins)
    # units_composition_obj.prepare_data()
    # res_str = units_composition_obj.make_str_logins(ctx.obj['FLAGS'])
    # print(res_str)
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(ctx.obj['prod_db']))
    user_obj = user_proxy.manager.get_obj(filters={"username": user})
    unit_proxy = db_sql.ProxyAction(db_sql.UnitManager(ctx.obj['prod_db']))
    units = unit_proxy.manager.get_objects(filters={"user_id": user_obj.id})
    # TODO Rewrite this using prettytable and include ctx.obj ['FLAGS']:
    for unit in units:
        print(unit.login)
    logger.info(f'Show logins command is done')


@cli.command()
@user_argument
@password_argument
@click.option('-l', "--login", prompt="Login", help="Provide login")
@click.option('-n', "--name", prompt="Name", help='name', default='default')
@click.pass_context
def get(ctx, user, password, login, name):
    """
    get password by login command
    """
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(ctx.obj['prod_db']))
    user_obj = user_proxy.manager.get_obj(filters={"username": user})
    unit_proxy = db_sql.ProxyAction(db_sql.UnitManager(ctx.obj['prod_db']))
    if unit_proxy.check_obj(filters={"user_id": user_obj.id, "login": login, "name": name}):
        pyperclip_copy(unit_proxy.get_secret(filters={
            "username": user,
            "password": password,
            "name": name,
            "login": login
        }))
        logger.info(f'Password is placed on the clipboard')
    else:
        msg_login_not_exist(login, name)
        exit(-1)


@cli.command()
@user_argument
@password_argument
@click.option('-l', "--login", prompt="Login", help="Provide login")
@click.option('-n', "--name", prompt="Name", help='name', default='default')
@click.pass_context
def delete(ctx, user, password, login, name):
    """
    delete login command
    """
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(ctx.obj['prod_db']))
    user_obj = user_proxy.manager.get_obj(filters={"username": user})
    unit_proxy = db_sql.ProxyAction(db_sql.UnitManager(ctx.obj['prod_db']))
    if unit_proxy.check_obj(filters={"user_id": user_obj.id, "login": login, "name": name}):
        unit_proxy.delete_obj(filters={
            "user_id": user_obj.id,
            "login": login,
            "name": name
        })
        logger.info(f'Login "{login}" deleted')
    else:
        msg_login_not_exist(login, name)
        exit(-1)


@cli.command()
@user_argument
@password_argument
@click.option('-l', "--login", prompt="Login", help="Provide login")
@click.option('-pl', "--password-for-login", prompt=True,
              help="Provide password for login", hide_input=True)
@click.option('-n', "--name", prompt="Name", help='name', default='default')
@click.option('-c', "--category", help='"default" or skip for default category, optional',
              default='default', required=False)
@click.option('-ur', "--url", help='url, optional', default='', required=False)
@click.pass_context
def add(ctx, user, password, login,
        password_for_login, name, category, url):
    """
    add login command
    """
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(ctx.obj['prod_db']))
    user_obj = user_proxy.manager.get_obj(filters={"username": user})
    unit_proxy = db_sql.ProxyAction(db_sql.UnitManager(ctx.obj['prod_db']))
    category_proxy = db_sql.ProxyAction(db_sql.CategoryManager(ctx.obj['prod_db']))
    if unit_proxy.check_obj(filters={"user_id": user_obj.id, "login": login, "name": name}):
        msg_login_exist(login, name)
        exit(-1)
    else:
        unit_proxy.add_obj({
            "username": user,
            "password": password,
            "name": name,
            "login": login,
            "secret": password_for_login,
            "user_id": user_obj.id,
            "category_id": category_proxy.get_prepared_category({
                "user_id": user_obj.id,
                "name": category
            }).id,
            "url": url
        })
        logger.info(f'Login "{login}" added')


@cli.command()
@user_argument
@password_argument
@click.option('-l', "--login", prompt="Login", help="Provide login")
@click.option('-n', "--name", prompt="Name", help='name', default='default')
@click.option('-nl', "--new-login", help='new login, optional',
              default=None, required=False)
@click.option('-nn', "--new-name", help='"default" or skip for old name, optional',
              default=None, required=False)
@click.option('-npl', "--new-password-for-login",
              prompt="New password for login (Press 'Enter' for keep old password)",
              default='',
              help="Provide new password for login", hide_input=True)
@click.option('-nc', "--new-category", help='"default" or skip for old category, optional',
              default=None, required=False)
@click.option('-nur', "--new-url", help='new url, optional', default=None, required=False)
@click.pass_context
def update(ctx, user, password, login, name,
           new_login, new_name, new_password_for_login, new_category, new_url):
    """
    update login command
    """
    user_proxy = db_sql.ProxyAction(db_sql.UserManager(ctx.obj['prod_db']))
    user_obj = user_proxy.manager.get_obj(filters={"username": user})
    unit_proxy = db_sql.ProxyAction(db_sql.UnitManager(ctx.obj['prod_db']))
    if unit_proxy.check_obj(filters={"user_id": user_obj.id, "login": login, "name": name}):
        if new_login != login or new_name != name:
            if unit_proxy.check_obj(filters={"user_id": user_obj.id, "login": new_login, "name": new_name}):
                msg_login_exist(new_login, new_name)
                exit(-1)
        data = {}
        if new_login:
            data["login"] = new_login
        if new_name:
            data["name"] = new_name
        if new_password_for_login != '':
            data["secret"] = new_password_for_login
            data["current_password"] = password
        if new_category:
            category_proxy = db_sql.ProxyAction(db_sql.CategoryManager(ctx.obj['prod_db']))
            data["category_id"] = category_proxy.get_prepared_category({
                "user_id": user_obj.id,
                "name": new_category
            }).id
        if new_url:
            data["url"] = new_url
        if data == {}:
            logger.info(f'Login not updated - nothing for update')
            exit(-1)
        unit_proxy.update_obj(
            filters={"user_id": user_obj.id, "login": login, "name": name},
            data=data
        )
        logger.info(f'Login "{login}" updated')
    else:
        msg_login_not_exist(login, name)
        exit(-1)


if __name__ == '__main__':
    cli()
