# -*- coding: utf-8 -*-
"""Sort packages in order of dependency.

This module implements sorting a list of package names in order of relative
dependency. That is if package B is a dependency of package A, B will occur
after A in the sorted list.

Todo:
    * ...
    * ...
"""

import networkx as nx
from Package import PackageInfo

def _inverse_bfs(graph):

  if 0== nx.number_of_nodes( graph ):
    return []

  leafs = [x for x in graph.nodes() if graph.out_degree(x)==0]

  graph.remove_nodes_from( leafs )

  return leafs + _inverse_bfs( graph )

# public API

def get_packages_inorder(packages, package_dependencies):
  """
  Given a list of packages, return the sorted list where a packages
  dependencies are listed before it.
  """

  pkg_graph = nx.DiGraph()

  for package, dependencies in zip(packages, package_dependencies):

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

  return _inverse_bfs( pkg_graph )
