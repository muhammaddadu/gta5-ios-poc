#!/usr/bin/env python3
"""Audit staged bytes, including force-added files; never read private directories."""
import pathlib
import re
import subprocess
import sys

ALLOWED = {'.gitignore', 'AGENTS.md', 'README.md', 'upstreams.json'}
EXTENSIONS = {'scripts': {'.py', '.sh'}, 'tests': {'.py'},
              'docs': {'.md'}, 'web': {'.html', '.js'}}


def audit():
    errors = []
    paths = subprocess.check_output(['git', 'ls-files', '-z']).split(b'\0')
    for raw in filter(None, paths):
        name = raw.decode()
        path = pathlib.PurePosixPath(name)
        allowed = name in ALLOWED or (len(path.parts) == 2 and
                  path.suffix in EXTENSIONS.get(path.parts[0], set()))
        if not allowed:
            errors.append(f'Not on source allowlist: {name}')
            continue
        mode = subprocess.check_output(['git', 'ls-files', '-s', '--', name]).split()[0]
        if mode not in (b'100644', b'100755'):
            errors.append(f'Non-regular file: {name}')
            continue
        body = subprocess.check_output(['git', 'show', ':' + name])
        if len(body) > 256 * 1024 or b'\0' in body:
            errors.append(f'Large/binary file: {name}')
        if re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', body):
            errors.append(f'Private key: {name}')
    return errors


if __name__ == '__main__':
    failures = audit()
    print('\n'.join(failures) if failures else 'Git index: source allowlist passed.')
    sys.exit(bool(failures))
