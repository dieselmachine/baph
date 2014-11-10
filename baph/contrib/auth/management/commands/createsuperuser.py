from __future__ import unicode_literals

import getpass
import sys
from optparse import make_option

from django.conf import settings
from django.core import exceptions

from django.utils.encoding import force_str
from django.utils.six.moves import input
from django.utils.text import capfirst

from baph.contrib.auth.management import get_default_username
from baph.core.management.base import BaseCommand, CommandError
from baph.db import DEFAULT_DB_ALIAS
from baph.db.orm import ORM


orm = ORM.get()

class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        # Options are defined in an __init__ method to support swapping out
        # custom user models in tests.
        from baph.contrib.auth.models import User
        super(Command, self).__init__(*args, **kwargs)
        self.UserModel = User
        self.AuthModel = getattr(User, 'AUTH_CLASS', User)
        self.username_field = None
        options = tuple([])

        if not settings.BAPH_AUTH_WITHOUT_USERNAMES:
            self.username_field = self.AuthModel._meta.get_field(
                self.UserModel.USERNAME_FIELD)
            options = (make_option('--%s' % self.AuthModel.USERNAME_FIELD,
                dest=self.UserModel.USERNAME_FIELD, default=None,
                help='Specifies the login for the superuser.'),)

        self.option_list = BaseCommand.option_list + options + (
            make_option('--noinput', action='store_false', dest='interactive',
                default=True,
                help=('Tells Django to NOT prompt the user for input of any '
                    'kind. You must pass an option for any required field. '
                    'Superusers created with --noinput will not be able to log '
                    'in until they\'re given a valid password.')),
        ) + tuple(
            make_option('--%s' % field, dest=field, default=None,
                help='Specifies the %s for the superuser.' % field)
            for field in self.UserModel.REQUIRED_FIELDS
        )

    option_list = BaseCommand.option_list
    help = 'Used to create a superuser.'

    def handle(self, *args, **options):
        interactive = options.get('interactive')
        verbosity = int(options.get('verbosity', 1))
        username = None
        if not settings.BAPH_AUTH_WITHOUT_USERNAMES:
            username = options.get(self.AuthModel.USERNAME_FIELD, None)

        # If not provided, create the user with an unusable password
        password = None
        user_data = {}

        # Do quick and dirty validation if --noinput
        if not interactive:
            try:
                if not settings.BAPH_AUTH_WITHOUT_USERNAMES:
                    if not username:
                        raise CommandError("You must use --%s with --noinput." %
                            self.AuthModel.USERNAME_FIELD)
                    username = self.username_field.clean(username, None)

                for field_name in self.AuthModel.REQUIRED_FIELDS:
                    if options.get(field_name):
                        field = self.AuthModel._meta.get_field(field_name)
                        user_data[field_name] = field.clean(options[field_name], None)
                    else:
                        raise CommandError("You must use --%s with --noinput." % field_name)
            except exceptions.ValidationError as e:
                raise CommandError('; '.join(e.messages))

        else:
            # Prompt for username/password, and any other required fields.
            # Enclose this whole thing in a try/except to trap for a
            # keyboard interrupt and exit gracefully.
            
            try:
                if not settings.BAPH_AUTH_WITHOUT_USERNAMES:
                # Get a username
                    default_username = get_default_username()
                    verbose_field_name = self.username_field.verbose_name
                    while username is None:
                        if not username:
                            input_msg = capfirst(verbose_field_name)
                            if default_username:
                                input_msg = "%s (leave blank to use '%s')" % (
                                    input_msg, default_username)
                            raw_value = input(force_str('%s: ' % input_msg))

                        if default_username and raw_value == '':
                            raw_value = default_username
                        try:
                            username = self.username_field.as_form_field().clean(raw_value)
                        except exceptions.ValidationError as e:
                            self.stderr.write("Error: %s" % '; '.join(e.messages))
                            username = None
                            continue

                        session = orm.sessionmaker()
                        user = session.query(self.AuthModel) \
                            .filter_by(username=username) \
                            .first()
                        if user:
                            self.stderr.write("Error: That %s is already taken." %
                                    verbose_field_name)
                            username = None
                    user_data[self.AuthModel.USERNAME_FIELD] = username

                for field_name in self.AuthModel.REQUIRED_FIELDS:
                    print 'required field:', field_name
                    field = self.AuthModel._meta.get_field(field_name)
                    user_data[field_name] = options.get(field_name)
                    while user_data[field_name] is None:
                        raw_value = input(force_str('%s: ' % capfirst(field.verbose_name)))
                        try:
                            user_data[field_name] = field.clean(raw_value)
                        except exceptions.ValidationError as e:
                            self.stderr.write("Error: %s" % '; '.join(e.messages))
                            user_data[field_name] = None

                # Get a password
                while password is None:
                    if not password:
                        password = getpass.getpass()
                        password2 = getpass.getpass(force_str('Password (again): '))
                        if password != password2:
                            self.stderr.write("Error: Your passwords didn't match.")
                            password = None
                            continue
                    if password.strip() == '':
                        self.stderr.write("Error: Blank passwords aren't allowed.")
                        password = None
                        continue

            except KeyboardInterrupt:
                self.stderr.write("\nOperation cancelled.")
                sys.exit(1)

        user_data['password'] = password
        self.AuthModel.create_superuser(**user_data)
        if verbosity >= 1:
            self.stdout.write("Superuser created successfully.")
