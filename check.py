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

def queryFileOwner(filename):

  p = subprocess.Popen(["pacman", "--noconfirm", "-Qo", filename], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
  data = p.communicate()

  stdout = data[0].decode()
  stderr = data[1].rstrip(b'\n').decode()

  if p.returncode != 0:
      raise Exception("Failed to get owner. {0}".format(stderr))

  return stdout.split()[-2]

def dependencies( filename ):

  p = subprocess.Popen(["ldd", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  dependencies = []

  for line in p.stdout.readlines():

    aux = line.decode().split()

    # avoid "not a dynamic executable"
    if aux[0] == "not":
      continue

    # ['name', 'hash']
    if len(aux) == 2:
      # ~ print(aux[0])
      continue # TODO chequear acá

    # ['name', '=>', 'path', 'hash']
    # ['name', '=>', 'not', 'found']
    elif len(aux) == 4:
      # ~ print(aux[0], aux[2])

      if aux[2]=="not":
        pkg = queryFileOwner( filename )
        print(pkg+":", filename, "depends on", aux[0], "which can't be found")

      elif not os.path.isfile(aux[2]):
        pkg = queryFileOwner( filename )
        print(pkg+":", filename, "depends on", aux[2], "which does not exist")

    else:
      print( aux )
      assert( False )

  return dependencies

def main(args):

  ####################
  ## load arguments ##
  ####################

  import argparse

  parser = argparse.ArgumentParser()

  parser.add_argument("root_dir", help="root dir to scan for outdated files")

  args = parser.parse_args()

  #######################################################
  ## Query and load dependencies into dependency graph ##
  #######################################################

  # ~ ret = set()

  for root, _, filenames in os.walk( args.root_dir ):
    for filename in filenames:
      filepath = os.path.join(root, filename)
      dependencies( filepath )

if __name__ == '__main__':
  import sys
  sys.exit(main(sys.argv))
