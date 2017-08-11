#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Concourse base resource class
"""
# Python 2 and 3 compatibility
from __future__ import unicode_literals, print_function

import os
import sys
import time
import json
import logging
import tempfile

import argparse
import subprocess


__program__ = "concourse-resource-type"
__version__ = "v0.1.0"
__author__ = "Jose Riguera"
__year__ = "2017"
__email__ = "jose.riguera@springernature.com"
__license__ = "MIT"
__purpose__ = "Consourse resource"



class Resource(object):
    """Base resource implementation."""
    LOGFORMAT='%(name)s: %(message)s'
    LOGGING="logging.ini"
    LOGLEVEL=logging.DEBUG
    LOGENVCONF="RESOURCE_CONFIGLOG"
    DEBUG="RESOURCE_DEBUG"


    def __init__(self, arguments=None, logging_config=None):
        # By default ansible logfile is used
        args = self._args(arguments)
        self._logging(logging_config)
        self.fdin = args.infile
        self.fdout = args.outfile
        self.workfolder = args.workfolder


    def _logging(self, config=None):
        logconf = False
        logpath = os.environ.get(self.LOGENVCONF, config)
        if logpath:
            logpath = os.path.expandvars(logpath)
            try:
                logging.config.fileConfig(logpath)
            except Exception as e:
                print("Error '%s': %s" % (logpath, e), file=sys.stderr)
                logging.basicConfig(level=self.LOGLEVEL, format=self.LOGFORMAT)
            else:
                logconf = True
        else:
            logfile = tempfile.NamedTemporaryFile(delete=False, prefix='log')
            logging.basicConfig(
                level=logging.DEBUG,
                format=self.LOGFORMAT,
                filename=logfile.name)
        if os.environ.get(self.DEBUG, "0").lower() in ['1', 'yes', 'true', 'y']:
            stderr = logging.StreamHandler()
            stderr.setLevel(level=logging.DEBUG)
            logging.getLogger().addHandler(stderr)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing " + str(self.__class__.__name__))
        if not logconf:
            self.logger.info("Using default logging settings")
        else:
            self.logger.info("Using logging settings from '%s'" % logpath)
        return self.logger


    def _args(self, arguments=None):
        epilog = __purpose__ + '\n'
        epilog += __version__ + ', ' + __year__ + ' '
        epilog += __author__ + ' ' + __email__
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            description=__doc__, epilog=epilog)
        g1 = parser.add_argument_group('Configuration options')
        g1.add_argument('workfolder', nargs='?')
        g1.add_argument('infile',
            nargs='?',
            type=argparse.FileType('r'),
            default=sys.stdin)
        g1.add_argument('outfile',
            nargs='?',
            type=argparse.FileType('w'),
            default=sys.stdout)
        args = parser.parse_args(arguments)
        return args


    def run(self, command):
        """Parse input/arguments, perform requested command return output."""
        try:
            input = json.loads(self.fdin.read())
        except ValueError as e:
            msg = "Input json data not well-formed: %s" % e
            self.logger.error(msg)
            raise ValueError(msg)
        # combine source and params
        source = input.get('source', {})
        params = input.get('params', {})
        version = input.get('version', {})
        # Debug
        if source.get('debug', False):
            self.logger.setLevel(logging.DEBUG)
        self.logger.debug('command: "%s"', command)
        self.logger.debug('input: "%s"', input)
        self.logger.debug('folder: "%s"', self.workfolder)
        self.logger.debug('environment: %s', os.environ)
        if command == 'check':
            try:
                rcode, response = self.check(source, version)
            except Exception as e:
                msg = "Exception running '%s': %s" % (command, str(e))
                self.logger.error(msg)
                raise
        else:
            if not self.workfolder:
                msg = "Workspace folder not provided"
                self.logger.error(msg)
                raise ValueError(msg)
            if command == 'in':
                try:
                    rcode, response = self.fetch(
                        self.workfolder, source, version, params)
                except Exception as e:
                    msg = "Exception running '%s': %s" % (command, str(e))
                    self.logger.error(msg)
                    raise
            elif command == 'out':
                try:
                    os.chdir(self.workfolder)
                except Exception as e:
                    self.logger.error(str(e))
                    raise
                try:
                    rcode, response = self.update(self.workfolder, source, params)
                except Exception as e:
                    msg = "Exception running '%s': %s" % (command, str(e))
                    self.logger.error(msg)
                    raise
            else:
                msg = "Invalid command: '%s'" % command
                self.logger.error(msg)
                raise ValueError(msg)
        self.logger.debug('response: "%s"', response)
        output = json.dumps(response, indent=4, separators=(',', ': '))
        self.fdout.write(str(output) + '\n')
        return rcode


    def metadata(self, result):
        metadata = []
        for k in result.keys():
            metadata.append({"name": str(k), "value": str(result[k]) })
        return metadata


    def process(self, cmd=[], input=None, timeout=None):
        proc = subprocess.Popen(cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.logger.info('Running process, pid=%d: %s' % (proc.pid, str(cmd)))
        try:
            output, err = proc.communicate(input, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            self.logger.warning(
                'Process %d killed with timeout %s' % (proc.pid, str(timeout)))
            proc.kill()
            output, err = proc.communicate()
        self.logger.debug("stdout: " + repr(output))
        self.logger.debug("stderr: " + repr(err))
        stdout = output.decode('utf-8')
        stderr = err.decode('utf-8')
        if proc.returncode != 0:
            self.logger.warning(
                'Process %d failed with rcode %d' % (proc.pid, int(proc.returncode)))
        else:
            self.logger.debug('Process %d finished with rcode 0' % (proc.pid))
        return int(proc.returncode), stdout, stderr


    def check(self, source, version):
        """`check` is invoked to detect new versions of the resource.

        `source` is an arbitrary JSON object which specifies the location of
        the resource, including any credentials. This is passed verbatim from
        the pipeline configuration.
        `version` is a JSON object with string fields, used to uniquely
        identify an instance of the resource.
        """
        timestamp = time.time()
        versions = { "timestamp": str(timestamp) }
        rvalue = [ versions ]
        rcode = 0
        return rcode, rvalue


    def fetch(self, dir, source, version, params):
        """`fetch` is passed a destination directory as $1, and is given on stdin
        the configured source and a precise version of the resource to fetch.

        `source` is the same value as passed to check.
        `version` is the same type of value passed to check, and specifies the
        version to fetch.

        `params` is an arbitrary JSON object passed along verbatim from params
        on a get.
        """
        metadata = []
        timestamp = time.time()
        ver = { "timestamp": str(timestamp) }
        rvalue = { "version": ver, "metadata": metadata }
        rcode = 0
        return rcode, rvalue


    def update(self, dir, source, params):
        """`update` is called with a path to the directory containing the
        build's full set of sources as the first argument, and is given on
        stdin the configured params and the resource's source configuration.

        `source` is the same value as passed to check.
        `params` is an arbitrary JSON object passed along verbatim from params
        on a put.
        """
        metadata = []
        timestamp = time.time()
        version = { "timestamp": str(timestamp) }
        rvalue = { "version": version, "metadata": metadata }
        rcode = 0
        return rcode, rvalue


if __name__ == '__main__':
    r = Resource()
    try:
        rcode = r.run(os.path.basename(__file__))
    except Exception as e:
        sys.stderr.write("ERROR: " + str(e) + "\n")
        sys.exit(1)
    sys.exit(rcode)

