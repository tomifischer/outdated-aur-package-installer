# -*- coding: utf-8 -*-
"""Package manager API.

Provide a python API for the local package manager in Arch Linux.

Todo:
    * ...
"""

import os
import subprocess

from Package import PackageInfo

PACKAGE_MANAGER = "yay"
"""str: The AUR package manager to use.
It should be able to manage the Arch User Repository (AUR) and be compliant with the pacman interface.
"""

def _pacman(flags, pkgs=[], eflgs=[], silent=True):
  """
  Subprocess wrapper for the package manager.
  src: https://github.com/peakwinter/python-pacman
  """

  # prepare command arguments

  if not pkgs:
    cmd = [PACKAGE_MANAGER, "--noconfirm", flags]
  elif type(pkgs) == list:
    cmd = [PACKAGE_MANAGER, "--noconfirm", flags]
    cmd += [quote(s) for s in pkgs]
  else:
    cmd = [PACKAGE_MANAGER, "--noconfirm", flags, pkgs]
  if eflgs and any(eflgs):
    eflgs = [x for x in eflgs if x]
    cmd += eflgs

  # call command

  p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE if silent else None)

  # retrieve return values

  ret = p.communicate()

  return {"code": p.returncode, "stdout": ret[0].decode() if silent else "", "stderr": ret[1].rstrip(b'\n').decode()}

def _sanitize_list_string(text, sep='\n'):
  """
  Convert a string representing a list of words into a clean list of words.
  """

  # split the text into words
  ls = text.split(sep=sep)

  # strip leading and trailing whitespace from words
  ls = map(str.strip, ls)

  # remove empty elements from the list
  ls = list(filter(None, ls))

  return ls

# public API

def is_found(package):
  """
  Returns True if the package is found in the package managers remote db.
  """
  return _pacman("-Q", package)["code"] == 0

def get_foreign_packages():
  """
  Get the list of foreign packages installed on the package manager database.
  """

  # -Q, --query    query package manager database
  # -q, --quiet    show less information for query and search
  # -m, --foreign  list installed packages not found in sync db(s)
  ret = _pacman('-Qqm')

  if ret["code"] != 0:
    raise Exception("Failed to query packages: {0}".format( ret["stderr"] ))

  return _sanitize_list_string( ret["stdout"] )

def get_installed_files(package):
  """
  Get the list the files owned by the queried package.
  """

  # -Q, --query    query package manager database
  # -q, --quiet    show less information for query and search
  # -l, --list     list the files owned by the queried package
  ret = _pacman('-Qql', package)

  if ret["code"] != 0:
    raise Exception("Failed to query package: {0}".format( ret["stderr"] ))

  return list(filter(os.path.isfile, _sanitize_list_string( ret["stdout"] )))

def get_package_info(package):

  # -Q, --query    query package manager database
  # -q, --quiet    show less information for query and search
  # -l, --list     list the files owned by the queried package
  ret = _pacman('-Qi', package)

  if ret["code"] != 0:
    raise Exception("Failed to query package: {0}".format( ret["stderr"] ))

  pkg_info = {}
  for line in ret["stdout"].strip().split('\n'):
    words = line.split(':')    
    pkg_info[ words[0].strip() ] = ':'.join( words[1:] ).strip()

  return pkg_info

def get_package_dependencies(package):

  pkg_info = get_package_info( package )

  return _sanitize_list_string(pkg_info["Depends On"], sep=None)

def install_package(package_name):

  ret = _pacman('-S', package_name, silent=False)

  if ret["code"] != 0:
    raise Exception("Failed to install package: {0}".format( ret["stderr"] ))
