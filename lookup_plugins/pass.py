#
# This script comes with ABSOLUTELY NO WARRANTY, use at own risk
# Copyright (C) 2017 mpv <ariel@gcoop.coop>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Ansible lookup plugin for ZXC24 password manager [0].
#
# To change the default password store set ANSIBLE_PASS_PASSWORD_STORE_DIR
# environment variable.
#
# If the pass doesn't exist in the store it's generated. It accepts two extra
# parameters: length and symbols (if symbols is True or yes -n is appended to
# the pass generate command).
#
# example: {{ lookup('pass', 'path/to/site lenght=20 symbols=False) }}
#
# [0] https://www.passwordstore.org/
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

import subprocess
import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.parsing.splitter import parse_kv

DEFAULT_PASSWORD_STORE_DIR = '~/.password-store'

PASS_EXEC = 'pass'

DEFAULT_LENGTH = 32
VALID_PARAMS = frozenset(('length', 'symbols', 'regenerate', 'password_dir'))

def _parse_parameters(term):
    # Hacky parsing of params taken from password lookup.
    first_split = term.split(' ', 1)
    if len(first_split) <= 1:
        # Only a single argument given, therefore it's a path
        name = term
        params = dict()
    else:
        name = first_split[0]
        params = parse_kv(first_split[1])
        if '_raw_params' in params:
            # Spaces in the path?
            name = ' '.join((name, params['_raw_params']))
            del params['_raw_params']

            # Check that we parsed the params correctly
            if not term.startswith(name):
                # Likely, the user had a non parameter following a parameter.
                # Reject this as a user typo
                raise AnsibleError('Unrecognized value after key=value parameters given to password lookup')
        # No _raw_params means we already found the complete path when
        # we split it initially

    # Check for invalid parameters.  Probably a user typo
    invalid_params = frozenset(params.keys()).difference(VALID_PARAMS)
    if invalid_params:
        raise AnsibleError('Unrecognized parameter(s) given to password lookup: %s' % ', '.join(invalid_params))

    # Set defaults
    PASS_EXEC = 'PASSWORD_STORE_DIR=%s pass' % params.get('password_dir', os.getenv('ANSIBLE_PASS_PASSWORD_STORE_DIR', DEFAULT_PASSWORD_STORE_DIR))
    params['length'] = int(params.get('length', DEFAULT_LENGTH))
    symbols = params.get('symbols', 'False')
    if symbols.lower() in ['true', 'yes']:
        params['symbols'] = True
    else:
        params['symbols'] = False
    regenerate = params.get('regenerate', 'False')
    if regenerate.lower() in ['true', 'yes']:
        params['regenerate'] = True
    else:
        params['regenerate'] = False

    return name, params


def get_password(path):
    """Get password from pass."""
    command = '%s show %s' % (PASS_EXEC, path)
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    if p.returncode == 0:
        return stdout.splitlines()[0].decode('utf-8')
    raise Exception(stderr)

def generate_password(path, length, symbols, force=False):
    """Generate password using pass."""
    command = '%s generate %s %s' % (PASS_EXEC, path, length)
    display.vvv('COMMAND: %s' % command)
    if not symbols:
        command = command + ' -n'
    if force:
        command = command + ' -f'

    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    if p.returncode != 0:
        raise Exception(stderr)

class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        ret = []

        for term in terms:
            '''
            http://docs.python.org/2/library/subprocess.html#popen-constructor
            The shell argument (which defaults to False) specifies whether to use the
            shell as the program to execute. If shell is True, it is recommended to pass
            args as a string rather than as a sequence
            https://github.com/ansible/ansible/issues/6550
            '''
            name, params = _parse_parameters(term)
            if params['regenerate']:
                try:
                    generate_password(name, params['length'], params['symbols'], True)
                    display.vvv('Generated password for %s' % name)
                except Exception as e:
                    raise AnsibleError("lookup_plugin.pass(%s) returned %s" % (term, e.message))

            try:
                password = get_password(term)
            except:
                try:
                    generate_password(name, params['length'], params['symbols'])
                    display.vvv('Generated password for %s' % name)
                    password = get_password(name)
                except Exception as e:
                    raise AnsibleError("lookup_plugin.pass(%s) returned %s" % (term, e.message))
            ret.append(password)
        return ret
