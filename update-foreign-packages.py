#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  outdated-aur-package-installer: Recompile AUR packages that rely
#    on old versions of updated libraries.
#
#  Copyright (C) 2017 Thomas Fischer
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import sys
import subprocess
from builtins import input

import object_deps
import package_depsort
import package_manager_api

def query_yes_no(question, default=None):
    """Ask a yes/no question via raw_input() and return their answer.
    
    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".

    src: http://code.activestate.com/recipes/577058/
    """

    if default == None:
      prompt = " [y/n] "
    elif default == True:
      prompt = " [Y/n] "
    elif default == False:
      prompt = " [y/N] "
    else:
      raise ValueError("invalid default answer: '%s'" % default)

    valid_true = ["y", "ye", "yes"]
    valid_false = ["n", "no"]

    while 1:

      choice = input(question + prompt).lower()

      if default is not None and choice == '':
        return default

      elif choice in valid_true:
        return True

      elif choice in valid_false:
        return False

      else:
        sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

def has_unresolved_dependencies(package, verbose=False):

  is_outdated = False

  installed_files = package_manager_api.get_installed_files( package )
  #print( installed_files )

  for filename in installed_files:
    unexisting_linked_libraries = object_deps.get_unexisting_linked_libraries( filename )
    is_outdated = is_outdated or (0 < len(unexisting_linked_libraries))

    # Only keep iterating if asked for verbose output, since in that case
    # we want to print all unresolved dependencies.

    if verbose:
      for unexisting_filename in unexisting_linked_libraries:
        print("  file " + filename + " depends on unexisting file " + unexisting_filename)

  return is_outdated

def main(args):

  ####################
  ## load arguments ##
  ####################

  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument("-p", "--package", help="Single package check.")
  parser.add_argument("-i", "--ignore", help="Ignore packages.", nargs='+')
  parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output.")
  parser.add_argument("-d", "--dryrun", action="store_true", help="Only list outdated packages without installing.")
  args = parser.parse_args()

  ######
  ##  ##
  ######

  if args.package:

    foreign_packages = [ args.package ]

  else:

    foreign_packages = package_manager_api.get_foreign_packages()

    package_dependencies = []
    for package in foreign_packages:
      package_dependencies.append( package_manager_api.get_package_dependencies( package ) )

    # update the "simpler" packages first, since packages that depend on
    # it may have unresolved links caused by the dependencies unresolved links.
    foreign_packages = package_depsort.get_packages_inorder(foreign_packages, package_dependencies)

  i_package = 1
  n_packages = len(foreign_packages)

  for package in foreign_packages:

    if args.ignore and package in args.ignore:
      continue

    print("Checking package " + str(i_package) + "/" + str(n_packages) + " " + package)

    if not package_manager_api.is_found( package ):
      print("WARNING, package " + package + " was not found.", file=sys.stderr)
      continue

    if has_unresolved_dependencies(package, args.verbose):

      print("package " + package + " needs to be reinstalled.")

      if args.dryrun:
        continue

      # package installation may fail. Wait for user input to continue.
      try:
        package_manager_api.install_package( package )

      except Exception as e:
        print( e )

        if not query_yes_no("continue?", True):
          return

    i_package += 1

if __name__ == '__main__':
  sys.exit( main( sys.argv ) )
