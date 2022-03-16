#!/usr/bin/env python

from ansible.parsing.dataloader import DataLoader

import os
import getpass
import sys
import logging
import argparse
import multiprocessing
import platform

from synckeys.list_keys.list_keys import list_keys
from synckeys.sync_projects.sync_projects import sync_acl


# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter
)

parser.add_argument(
    '--key-name',
    default=getpass.getuser(),
    help='The name of your key in the file containing all keys'
)

parser.add_argument(
    '--project',
    default=None,
    help='Sync a particular project'
)
parser.add_argument(
    '--acl',
    default=os.path.join(os.getcwd(), 'acl.yml'),
    help='Name of the file containing all access informations'
)

parser.add_argument(
    '--keys',
    default=os.path.join(os.getcwd(), 'keys.yml'),
    help='Name of the file containing all keys'
)

parser.add_argument(
    '--logging-level',
    default='INFO'
)

parser.add_argument(
    '--dry-run',
    dest='dry_run',
    action="store_true",
    default=False
)

parser.add_argument(
    '--private-key',
    dest='private_key'
)

parser.add_argument(
    '--list-keys',
    dest='list_keys',
    action='store_true',
    default=False
)


def main(argv=None):
    if platform.system() == "Darwin":
        multiprocessing.set_start_method("fork")
    if not argv:
        argv = sys.argv

    # Parse the command-line flags.
    flags = parser.parse_args(argv[1:])

    # set logging level
    logging.basicConfig(level=getattr(logging, flags.logging_level), format="%(message)s")

    dl = DataLoader()
    # load data
    acl = dl.load_from_file(flags.acl)['acl']
    keys = dl.load_from_file(flags.keys)['keys']

    if flags.list_keys:
        list_keys(dl, acl, flags.key_name, flags.project, flags.private_key, flags.dry_run)
        return

    sync_acl(dl, acl, keys, flags.key_name, flags.project, flags.dry_run, flags.private_key)


if __name__ == '__main__':
    main(sys.argv)
