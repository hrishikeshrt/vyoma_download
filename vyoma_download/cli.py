#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Console script for vyoma_download."""

###############################################################################

import os
import sys
import stat
import getpass
import logging
import argparse

from tabulate import tabulate

from . import __version__
from .verbose_logger import VERBOSE, install as install_logger
from .vyoma import Vyoma

###############################################################################

install_logger()

# --------------------------------------------------------------------------- #

ROOT_LOGGER = logging.getLogger()
ROOT_LOGGER.addHandler(logging.StreamHandler()),
ROOT_LOGGER.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #

LOGGER = logging.getLogger(__name__)

###############################################################################


def main():
    desc = "Download course contents from 'sanskritfromhome.in'."

    p = argparse.ArgumentParser(description=desc)
    p.add_argument("course-pattern", help="URL of the relevant course")
    p.add_argument("-a", "--audio", action='store_true',
                   help="Download audios only")
    p.add_argument("-d", "--document", action='store_true',
                   help="Download documents only")
    p.add_argument("-o", "--output", default=None,
                   help="Path to the download directory")
    p.add_argument("-u", "--username", default=None)
    p.add_argument("-p", "--password", default=None)
    p.add_argument('--status',
                   help="Display status of the current course",
                   action="store_true")
    p.add_argument('--verbose',
                   help="Enable verbose output",
                   action="store_true")
    p.add_argument('--debug',
                   help="Enable debug information",
                   action="store_true")
    p.add_argument('--version',
                   action="version",
                   version='%(prog)s ' + __version__)

    args = vars(p.parse_args())

    if args['verbose']:
        ROOT_LOGGER.setLevel(VERBOSE)
    if args['debug']:
        ROOT_LOGGER.setLevel(logging.DEBUG)

    # credentials
    config = {}

    home_dir = os.path.expanduser('~')
    config_file = os.path.join(home_dir, '.vyoma.cfg')
    if os.path.isfile(config_file):
        with open(config_file) as f:
            lines = f.read().split('\n')
            for line in lines:
                if line.strip():
                    key, value = line.split('=')
                config[key.strip()] = value.strip()

    username = (
        args['username'] or
        os.environ.get('VYOMA_USER') or
        config.get('username')
    )
    password = (
        args['password'] or
        os.environ.get('VYOMA_PASS') or
        config.get('password')
    )
    manual = not (username and password)

    if not username:
        username = input('Username: ')
    if not password:
        password = getpass.getpass('Password: ')
    username = username.strip()
    password = password.strip()

    # action
    vyoma_session = Vyoma(
        username=username,
        password=password,
        download_dir=args['output']
    )
    if not vyoma_session.logged_in:
        logging.error("Could not sign-in. Are the credentials correct?")
        return 1

    if manual:
        answer = input("Save credentials for future use? (Y/n)")
        if not answer or answer.lower()[0] == 'y':
            with open(config_file, 'w') as f:
                f.write(f"username = {username}\n"
                        f"password = {password}")
            logging.info("Credentials saved!")
            os.chmod(config_file, stat.S_IREAD + stat.S_IWRITE)

    if vyoma_session.logged_in:
        courses = vyoma_session.find_course(args['course-pattern'])
        if courses:
            print(tabulate(courses, headers={
                "course_id": "ID",
                "course_name": "Name",
                "course_instructor": "Teacher"
            }, tablefmt="fancy_grid", showindex="always"))
            while True:
                prompt = "Please choose the course index (default: 0): "
                selection = input(prompt)
                if not selection:
                    selection = '0'
                if selection not in map(str, range(len(courses))):
                    ROOT_LOGGER.error("Invalid selection.")
                else:
                    selection = int(selection)
                    course_id = courses[selection]["course_id"]
                    break

        if args["status"]:
            vyoma_session.show_course_status(course_id)
            return 0

        if not(any([args["audio"], args["document"]])):
            vyoma_session.download_course(
                course_id,
                fetch_audio=True,
                fetch_document=True
            )
        else:
            vyoma_session.download_course(
                course_id,
                fetch_audio=args["audio"],
                fetch_document=args["document"]
            )

    return 0

###############################################################################


if __name__ == "__main__":
    sys.exit(main())

###############################################################################
