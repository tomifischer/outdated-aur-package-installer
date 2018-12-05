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
import networkx as nx

# The package manager to use. It should be able to manage the
# Arch User Repository (AUR) and be compliant with the pacman interface.
PACKAGE_MANAGER = "yay"

def sanitize_list_string(text, sep='\n'):
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

def pacman(flags, pkgs=[], eflgs=[]):
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

  p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

  # retrieve return values

  ret = p.communicate()

  return {"code": p.returncode, "stdout": ret[0].decode(), "stderr": ret[1].rstrip(b'\n').decode()}

def is_found(package):
  """
  Returns True if the package is found in the package managers remote db.
  """
  return pacman("-Q", package)["code"] == 0

def get_foreign_packages():
  """
  Get the list of foreign packages installed on the package manager database.
  """

  # -Q, --query    query package manager database
  # -q, --quiet    show less information for query and search
  # -m, --foreign  list installed packages not found in sync db(s)
  ret = pacman('-Qqm')

  if ret["code"] != 0:
    raise Exception("Failed to query packages: {0}".format( ret["stderr"] ))

  return sanitize_list_string( ret["stdout"] )

def get_installed_files(package):
  """
  Get the list the files owned by the queried package.
  """

  # -Q, --query    query package manager database
  # -q, --quiet    show less information for query and search
  # -l, --list     list the files owned by the queried package
  ret = pacman('-Qql', package)

  if ret["code"] != 0:
    raise Exception("Failed to query package: {0}".format( ret["stderr"] ))

  return list(filter(os.path.isfile, sanitize_list_string( ret["stdout"] )))

def get_package_info(package):

  # -Q, --query    query package manager database
  # -q, --quiet    show less information for query and search
  # -l, --list     list the files owned by the queried package
  ret = pacman('-Qi', package)

  if ret["code"] != 0:
    raise Exception("Failed to query package: {0}".format( ret["stderr"] ))

  pkg_info = {}
  for line in ret["stdout"].strip().split('\n'):
    words = line.split(':')    
    pkg_info[ words[0].strip() ] = ':'.join( words[1:] ).strip()

  return pkg_info

def get_package_dependencies(package):

  pkg_info = get_package_info( package )

  return sanitize_list_string(pkg_info["Depends On"], sep=None)

def ldd_object_exists(binary_filename, ldd_line):

  # this should be the absolute path to the object
  path = ldd_line.split()[-2]

  # some kernel specific objects don't show the absolute path
  if path.startswith("linux-vdso.so") or path.startswith("linux-gate.so"):
    return True

  # some executables apparently set their own LD_LIBRARY_PATH for their own
  # shared objects on startup, which are referenced relatively.
  if not path.startswith('/'):
    return True

  return os.path.exists( path )

def get_unexisting_linked_libraries(binary_filename):

  p = subprocess.Popen(["ldd", binary_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  ret = p.communicate()

  # ldd may fail if the file is a directory or if the script
  # does not have execution permission.
  if p.returncode != 0:
    #print("{0}".format( ret[1].rstrip(b'\n').decode() ))
    #raise Exception("Failed to query shared objects: {0}".format( ret[1].rstrip(b'\n').decode() ))
    return []

  # get the list of linked objects
  ls = sanitize_list_string( ret[0].decode() )

  # filter out objects that do not exist
  ls = list(filter(lambda dep: not ldd_object_exists(binary_filename, dep), ls))

  return ls

def inverse_bfs(graph):

  if 0== nx.number_of_nodes( graph ):
    return []

  leafs = [x for x in graph.nodes() if graph.out_degree(x)==0]

  graph.remove_nodes_from( leafs )

  return leafs + inverse_bfs( graph )

def get_packages_inorder(packages):
  """
  Given a list of packages, return the sorted list where a packages
  dependencies are listed before it.
  """

  pkg_graph = nx.DiGraph()

  for package in packages:

    pkg_info = get_package_info( package )

    dependencies = get_package_dependencies( package )

    # (tfischer) I don't remember why I didn't update the pkg_graph directly
    # when I wrote this, but I think there was a reason.
    # maybe because of duplicates?
    aux_graph = nx.DiGraph()
    aux_graph.add_node( package )
    for dependency in dependencies:
      if dependency in packages:
        aux_graph.add_node( dependency )
        aux_graph.add_edge( package, dependency )

    pkg_graph = nx.compose(pkg_graph, aux_graph)

  assert( len(list(nx.simple_cycles(pkg_graph))) == 0 )

  return inverse_bfs( pkg_graph )

def has_unresolved_dependencies(package, verbose=False):

  is_outdated = False

  installed_files = get_installed_files( package )
  #print( installed_files )

  for filename in installed_files:
    unexisting_linked_libraries = get_unexisting_linked_libraries( filename )
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
  parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output.")
  parser.add_argument("-d", "--dry-run", action="store_true", help="Only list outdated packages without installing.")
  args = parser.parse_args()

  ######
  ##  ##
  ######

  foreign_packages = get_foreign_packages()
  #print( foreign_packages )

  # update the "simpler" packages first, since packages that depend on
  # it may have unresolved links caused by the dependencies unresolved links.
  foreign_packages = get_packages_inorder( foreign_packages )
  #print( foreign_packages )

  i_package = 1
  n_packages = len(foreign_packages)

  for package in foreign_packages:

    print("Checking package " + str(i_package) + "/" + str(n_packages) + " " + package)

    if not is_found( package ):
      print("WARNING, package " + package + " was not found.", file=sys.stderr)
      continue

    if has_unresolved_dependencies(package, args.verbose):
      print("package " + package + " needs to be reinstalled.")
      # TODO update package

    i_package += 1

if __name__ == '__main__':
  import sys
  sys.exit( main( sys.argv ) )
