# -*- coding: utf-8 -*-

import os
import subprocess

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

def _ldd_object_exists(binary_filename, ldd_line):

  # each entry should read
  # <PATH> (<HASH?>)
  # <NAME> => <PATH> (<HASH?>)
  # <NAME> => not found
  data = ldd_line.split()

  if len(data) != 2 and len(data) != 4:
    print("WARNING ldd output format not recognized: '" + ldd_line + "'. Ignoring object!")
    return True

  if len(data) == 4 and data[2] == "not" and data[3] == "found":
    return False

  # this should be the absolute path for len=4 entries,
  # or the object name for len=2 entries
  object_path = data[-2]

  if len(data) == 2:

    # some kernel specific objects don't show the absolute path
    if object_path.startswith("linux-vdso.so") or object_path.startswith("linux-gate.so"):
      return True

    # some executables apparently set their own LD_LIBRARY_PATH for their own
    # shared objects on startup, which are referenced relatively.
    if not object_path.startswith('/'):
      return True

  return os.path.exists( object_path )

# public API

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
  ls = _sanitize_list_string( ret[0].decode() )
  #print("\n".join(ls))

  # filter out objects that do not exist
  ls = list(filter(lambda dep: not _ldd_object_exists(binary_filename, dep), ls))

  return ls
