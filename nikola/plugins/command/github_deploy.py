# -*- coding: utf-8 -*-

# Copyright © 2014 Puneeth Chaganti and others.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import print_function
import os
import subprocess
import sys
from textwrap import dedent

from nikola.plugin_categories import Command
from nikola.plugins.command.check import real_scan_files
from nikola.utils import get_logger, req_missing
from nikola.__main__ import main
from nikola import __version__


def uni_check_output(*args, **kwargs):
    o = subprocess.check_output(*args, **kwargs)
    return o.decode('utf-8')


def check_ghp_import_installed():
    try:
        subprocess.check_output(['ghp-import', '-h'])
    except OSError:
        req_missing('ghp-import', 'deploy the site to GitHub pages')


class CommandGitHubDeploy(Command):
    """ Deploy site to GitHub pages. """
    name = 'github_deploy'

    doc_usage = ''
    doc_purpose = 'deploy the site to GitHub pages'
    doc_description = dedent(
        """\
        This command can be used to deploy your site to GitHub pages.

        It uses ghp-import to do this task.

        """
    )

    logger = None

    _deploy_branch = ''
    _source_branch = ''
    _remote_name = ''

    def _execute(self, command, args):

        self.logger = get_logger(
            CommandGitHubDeploy.name, self.site.loghandlers
        )
        self._source_branch = self.site.config.get(
            'GITHUB_SOURCE_BRANCH', 'master'
        )
        self._deploy_branch = self.site.config.get(
            'GITHUB_DEPLOY_BRANCH', 'gh-pages'
        )
        self._remote_name = self.site.config.get(
            'GITHUB_REMOTE_NAME', 'origin'
        )
        self._pull_before_commit = self.site.config.get(
            'GITHUB_PULL_BEFORE_COMMIT', False
        )

        # Check if ghp-import is installed
        check_ghp_import_installed()

        # Build before
        build = main(['build'])
        if build != 0:
            self.logger.error('Build failed, not deploying to GitHub')
            sys.exit(build)

        # Clean non-target files
        only_on_output, _ = real_scan_files(self.site)
        for f in only_on_output:
            os.unlink(f)

        # Commit and push
        self._commit_and_push()

        return

    def _commit_and_push(self):
        """ Commit all the files and push. """

        deploy = self._deploy_branch
        source = self._source_branch
        remote = self._remote_name

        source_commit = uni_check_output(['git', 'rev-parse', source])
        commit_message = (
            'Nikola auto commit.\n\n'
            'Source commit: %s'
            'Nikola version: %s' % (source_commit, __version__)
        )
        output_folder = self.site.config['OUTPUT_FOLDER']

        command = ['ghp-import', '-n', '-m', commit_message, '-p', '-r', remote, '-b', deploy, output_folder]

        self.logger.info("==> {0}".format(command))
        try:
            subprocess.check_call(command)
        except subprocess.CalledProcessError as e:
            self.logger.error(
                'Failed GitHub deployment — command {0} '
                'returned {1}'.format(e.cmd, e.returncode)
            )
            sys.exit(e.returncode)
