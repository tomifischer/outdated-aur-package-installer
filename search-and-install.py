#!/usr/bin/env python3
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
import subprocess
import networkx as nx

def queryPackageInfo(package_name):

  p = subprocess.Popen(["pacman", "--noconfirm", "-Qi", package_name], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
  data = p.communicate()

  stdout = data[0].decode()
  stderr = data[1].rstrip(b'\n').decode()

  if p.returncode != 0:
      raise Exception("Failed to get info. {0}".format(stderr))

  pkg_info = {}
  for line in stdout.strip().split('\n'):
    words = line.split(':')    
    pkg_info[ words[0].strip() ] = ':'.join( words[1:] ).strip()

  return pkg_info

def queryFileOwner(filename):

  p = subprocess.Popen(["pacman", "--noconfirm", "-Qo", filename], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
  data = p.communicate()

  stdout = data[0].decode()
  stderr = data[1].rstrip(b'\n').decode()

  if p.returncode != 0:
      raise Exception("Failed to get owner. {0}".format(stderr))

  return stdout.split()[-2]

def installPackage(package_name):

  p = subprocess.Popen(["yaourt", "--noconfirm", "-S", package_name], stderr=subprocess.PIPE)
  data = p.communicate()

  # communicate() returns a tuple (stdout_data, stderr_data).
  #stdout = data[0].decode()
  stderr = data[1].rstrip(b'\n').decode()

  if p.returncode != 0:
      raise Exception("Failed to install package. {0}".format(stderr))

def dependsOn(library_filename, dependency_name, version):

  p = subprocess.Popen(["ldd", library_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  dependencies = []

  for line in p.stdout.readlines():

    aux = line.decode().split()

    if (dependency_name in aux[0]) and (version in aux[0]):
      return True

  return False

def loadPackagesFromFile( filename ):
  with open( filename ) as f:
    words = f.read().split()
    return set(words)

def searchForPackages(root_dir, dependency_name, dependency_version):
  ret = set()
  for root, _, filenames in os.walk( root_dir ):
    for filename in filenames:
      filepath = os.path.join(root, filename)
      if ( dependsOn(filepath, dependency_name, dependency_version) ):
        ret.add( queryFileOwner(filepath) )
  return ret

def getInverseBFS(graph):

  if 0== nx.number_of_nodes( graph ):
    return []

  leafs = [x for x in graph.nodes() if graph.out_degree(x)==0]

  graph.remove_nodes_from( leafs )

  return leafs + getInverseBFS( graph )

def main(args):

  ####################
  ## load arguments ##
  ####################

  import argparse

  parser = argparse.ArgumentParser()

  parser.add_argument("root_dir", help="root dir to scan for outdated files")
  parser.add_argument("dependency_name", help="dependency name to scan for. Example: boost")
  parser.add_argument("dependency_version", help="dependency version to scan for. Example: 1.63")
  parser.add_argument("-i", "--install", action="store_true", help="install outdated packages")

  args = parser.parse_args()

  #######################################################
  ## Query and load dependencies into dependency graph ##
  #######################################################

  print("searching for outdated files...")
  packages = searchForPackages(args.root_dir, args.dependency_name, args.dependency_version)

  print("computing dependency graph...")
  pkg_graph = nx.DiGraph()
  for package in packages:

    pkg_info = queryPackageInfo( package )

    pkg_name = pkg_info["Name"]
    dependencies = pkg_info["Depends On"].split()

    aux_graph = nx.DiGraph()
    aux_graph.add_node( pkg_name )
    for dependency in dependencies:
      if dependency in packages:
        aux_graph.add_node( dependency )
        aux_graph.add_edge( pkg_name, dependency )

    pkg_graph = nx.compose(pkg_graph, aux_graph)

  ####################################
  ## Show packages in install order ##
  ####################################

  assert( len(list(nx.simple_cycles(pkg_graph))) == 0 )

  sorted_pkgs = getInverseBFS( pkg_graph )

  if args.install:
    print("installing outdated packages...")
    i = 0
    n = len(sorted_pkgs)
    for pkg in sorted_pkgs:
      print(str(i) + "/" + str(n), pkg)
      installPackage( pkg )
      i = i+1
  else:
    print(' '.join( sorted_pkgs ))

  return 0

if __name__ == '__main__':
  import sys
  sys.exit(main(sys.argv))
