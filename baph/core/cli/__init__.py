from __future__ import unicode_literals

from argparse import ArgumentParser
from collections import defaultdict
from importlib import import_module
import os
import pkgutil
import sys

from click.core import BaseCommand
from click.testing import CliRunner
from flask import current_app
from flask.cli import FlaskGroup
import six

import baph
from baph.apps import apps
from baph.conf import settings
from baph.conf.preconfigure import Preconfigurator
from baph.core.exceptions import ImproperlyConfigured
from baph.core.cli.color import color_style
from baph.utils import lru_cache
from baph.utils._os import npath, upath


def find_commands(management_dir):
  """
  Given a path to a management directory, returns a list of all the command
  names that are available.

  Returns an empty list if no commands are defined.
  """
  command_dir = os.path.join(management_dir, 'commands')
  #print 'cmd dir:', command_dir
  return [name for _, name, is_pkg in pkgutil.iter_modules([npath(command_dir)])
          if not is_pkg and not name.startswith('_')]

def load_command_class(app_name, name):
    """
    Given a command name and an application name, returns the Command
    class instance. All errors raised by the import process
    (ImportError, AttributeError) are allowed to propagate.
    """
    module = import_module('%s.commands.%s' % (app_name, name))
    return module.Command()

@lru_cache.lru_cache(maxsize=None)
def get_commands():
  """
  Returns a dictionary mapping command names to their callback applications.

  This works by looking for a management.commands package in django.core, and
  in each installed application -- if a commands package exists, all commands
  in that package are registered.

  Core commands are always included. If a settings module has been
  specified, user-defined commands will also be included.

  The dictionary is in the format {command_name: app_name}. Key-value
  pairs from this dictionary can then be used in calls to
  load_command_class(app_name, command_name)

  If a specific version of a command must be loaded (e.g., with the
  startapp command), the instantiated module can be placed in the
  dictionary in place of the application name.

  The dictionary is cached on the first call and reused on subsequent
  calls.
  """
  #print 'current app:', current_app
  baph.setup()
  cli = FlaskGroup(__name__, create_app=baph.create_app)

  #commands = {name: 'django.core' for name in find_commands(upath(__path__[0]))}
  commands = {name: 'flask' for name in cli.commands}

  if not settings.configured:
    return commands

  for app_config in reversed(list(apps.get_app_configs())):
    #print 'app config:', app_config
    #path = os.path.join(app_config.path, 'management')
    path = app_config.path
    commands.update({name: app_config.name for name in find_commands(path)})

  return commands

def handle_default_options(options):
  """
  Include any default options that all commands should accept here
  so that ManagementUtility can handle them before searching for
  user commands.
  """
  if options.settings:
    os.environ['FLASK_SETTINGS_MODULE'] = options.settings
  if options.pythonpath:
    sys.path.insert(0, options.pythonpath)
  preconfig = Preconfigurator()
  for setting in preconfig.core_settings:
    if getattr(options, setting, None):
      os.environ[setting] = getattr(options, setting)

class ManagementUtility(object):
  """
  Encapsulates the logic of the django-admin and manage.py utilities.

  A ManagementUtility has a number of commands, which can be manipulated
  by editing the self.commands dictionary.
  """
  def __init__(self, argv=None):
    self.argv = argv or sys.argv[:]
    self.prog_name = os.path.basename(self.argv[0])
    self.settings_exception = None

  def main_help_text(self, commands_only=False):
    """
    Returns the script's main help text, as a string.
    """
    if commands_only:
        usage = sorted(get_commands().keys())
    else:
        usage = [
            "",
            "Type '%s help <subcommand>' for help on a specific subcommand." % self.prog_name,
            "",
            "Available subcommands:",
        ]
        commands_dict = defaultdict(lambda: [])
        for name, app in six.iteritems(get_commands()):
            if app == 'django.core':
                app = 'django'
            else:
                app = app.rpartition('.')[-1]
            commands_dict[app].append(name)
        style = color_style()
        for app in sorted(commands_dict.keys()):
            usage.append("")
            usage.append(style.NOTICE("[%s]" % app))
            for name in sorted(commands_dict[app]):
                usage.append("    %s" % name)
        # Output an extra note if settings are not properly configured
        if self.settings_exception is not None:
            usage.append(style.NOTICE(
                "Note that only Django core commands are listed "
                "as settings are not properly configured (error: %s)."
                % self.settings_exception))

    return '\n'.join(usage)

  def fetch_command(self, subcommand):
    """
    Tries to fetch the given subcommand, printing a message with the
    appropriate command called from the command line (usually
    "django-admin" or "manage.py") if it can't be found.
    """
    # Get commands outside of try block to prevent swallowing exceptions
    commands = get_commands()
    try:
        app_name = commands[subcommand]
    except KeyError:
        if os.environ.get('FLASK_SETTINGS_MODULE'):
            # If `subcommand` is missing due to misconfigured settings, the
            # following line will retrigger an ImproperlyConfigured exception
            # (get_commands() swallows the original one) so the user is
            # informed about it.
            settings.INSTALLED_APPS
        else:
            sys.stderr.write("No Django settings specified.\n")
        sys.stderr.write(
            "Unknown command: %r\nType '%s help' for usage.\n"
            % (subcommand, self.prog_name)
        )
        sys.exit(1)
    if isinstance(app_name, BaseCommand):
        # If the command is already loaded, use it directly.
        klass = app_name
    else:
        klass = load_command_class(app_name, subcommand)
    return klass

  def autocomplete(self):
    """
    Output completion suggestions for BASH.

    The output of this function is passed to BASH's `COMREPLY` variable and
    treated as completion suggestions. `COMREPLY` expects a space
    separated string as the result.

    The `COMP_WORDS` and `COMP_CWORD` BASH environment variables are used
    to get information about the cli input. Please refer to the BASH
    man-page for more information about this variables.

    Subcommand options are saved as pairs. A pair consists of
    the long option string (e.g. '--exclude') and a boolean
    value indicating if the option requires arguments. When printing to
    stdout, an equal sign is appended to options which require arguments.

    Note: If debugging this function, it is recommended to write the debug
    output in a separate file. Otherwise the debug output will be treated
    and formatted as potential completion suggestions.
    """
    # Don't complete if user hasn't sourced bash_completion file.
    if 'DJANGO_AUTO_COMPLETE' not in os.environ:
        return

    cwords = os.environ['COMP_WORDS'].split()[1:]
    cword = int(os.environ['COMP_CWORD'])

    try:
        curr = cwords[cword - 1]
    except IndexError:
        curr = ''

    subcommands = list(get_commands()) + ['help']
    options = [('--help', False)]

    # subcommand
    if cword == 1:
        print(' '.join(sorted(filter(lambda x: x.startswith(curr), subcommands))))
    # subcommand options
    # special case: the 'help' subcommand has no options
    elif cwords[0] in subcommands and cwords[0] != 'help':
        subcommand_cls = self.fetch_command(cwords[0])
        # special case: add the names of installed apps to options
        if cwords[0] in ('dumpdata', 'sqlmigrate', 'sqlsequencereset', 'test'):
            try:
                app_configs = apps.get_app_configs()
                # Get the last part of the dotted path as the app name.
                options.extend((app_config.label, 0) for app_config in app_configs)
            except ImportError:
                # Fail silently if DJANGO_SETTINGS_MODULE isn't set. The
                # user will find out once they execute the command.
                pass
        parser = subcommand_cls.create_parser('', cwords[0])
        options.extend(
            (sorted(s_opt.option_strings)[0], s_opt.nargs != 0)
            for s_opt in parser._actions if s_opt.option_strings
        )
        # filter out previously specified options from available options
        prev_opts = [x.split('=')[0] for x in cwords[1:cword - 1]]
        options = [opt for opt in options if opt[0] not in prev_opts]

        # filter options by current input
        options = sorted((k, v) for k, v in options if k.startswith(curr))
        for option in options:
            opt_label = option[0]
            # append '=' to options which require args
            if option[1]:
                opt_label += '='
            print(opt_label)
    # Exit code of the bash completion function is never passed back to
    # the user, so it's safe to always exit with 0.
    # For more details see #25420.
    sys.exit(0)

  def execute(self):
    """
    Given the command-line arguments, this figures out which subcommand is
    being run, creates a parser appropriate to that command, and runs it.
    """
    # Preprocess options to extract --settings and --pythonpath.
    # These options could affect the commands that are available, so they
    # must be processed early.
    #parser = CommandParser(None, usage="%(prog)s subcommand [options] [args]", add_help=False)
    parser = ArgumentParser()
    parser.add_argument('--settings')
    parser.add_argument('--pythonpath')

    # load user-defined pre-processing parameters
    preconfig = Preconfigurator()
    preconfig.add_arguments(parser)

    parser.add_argument('args', nargs='*')  # catch-all
    try:
      options, args = parser.parse_known_args(self.argv[1:])
      handle_default_options(options)
    except Exception as e:
      pass  # Ignore any option errors at this point.

    try:
      subcommand = options.args[0]
    except IndexError:
      subcommand = 'help'  # Display help if no arguments were given.

    no_settings_commands = [
      'help', 'version', '--help', '--version', '-h',
      'compilemessages', 'makemessages',
      'startapp', 'startproject',
    ]

    try:
      settings.INSTALLED_APPS
    except ImproperlyConfigured as exc:
      self.settings_exception = exc
      # A handful of built-in management commands work without settings.
      # Load the default settings -- where INSTALLED_APPS is empty.
      if subcommand in no_settings_commands:
        settings.configure()

    if settings.configured:
      # Start the auto-reloading dev server even if the code is broken.
      # The hardcoded condition is a code smell but we can't rely on a
      # flag on the command class because we haven't located it yet.
      if subcommand == 'runserver' and '--noreload' not in self.argv:
        try:
          autoreload.check_errors(django.setup)()
        except Exception:
          # The exception will be raised later in the child process
          # started by the autoreloader. Pretend it didn't happen by
          # loading an empty list of applications.
          apps.all_models = defaultdict(OrderedDict)
          apps.app_configs = OrderedDict()
          apps.apps_ready = apps.models_ready = apps.ready = True

      # In all other cases, django.setup() is required to succeed.
      else:
        baph.setup()

    self.autocomplete()

    import click
    @click.group(cls=FlaskGroup, create_app=baph.create_app)
    def cli(**kwargs):
      pass

    print '\ncli:', cli

    if subcommand == 'help':
      print 'help subcommand'
      print '  args:', args
      print '  options:', options
      if '--commands' in args:
        sys.stdout.write(self.main_help_text(commands_only=True) + '\n')
      elif len(options.args) < 2:
        sys.stdout.write(self.main_help_text() + '\n')
      else:
        self.fetch_command(options.args[1]) \
            .print_help(self.prog_name, options.args[1])
    # Special-cases: We want 'django-admin --version' and
    # 'django-admin --help' to work, for backwards compatibility.
    elif subcommand == 'version' or self.argv[1:] == ['--version']:
        sys.stdout.write(django.get_version() + '\n')
    elif self.argv[1:] in (['--help'], ['-h']):
        sys.stdout.write(self.main_help_text() + '\n')
    else:
      print 'running subcommand'
      print '  args:', args
      cli.main(args=[subcommand] + args, prog_name='test')

      #self.fetch_command(subcommand).run_from_argv(self.argv)

def execute_from_command_line(argv=None):
  """
  A simple method that runs a ManagementUtility.
  """
  print 'execute from command line:'
  print '  argv:', argv
  utility = ManagementUtility(argv)
  utility.execute()