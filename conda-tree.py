#!/usr/bin/env python
from __future__ import print_function
import argparse
import json
import os
import sys
import subprocess

import conda.exports
import networkx

__version__ = '0.0.5'

def get_local_cache(prefix):
	return conda.exports.linked_data(prefix=prefix)

def get_package_key(cache, package_name):
	ks = list(filter(lambda i: l[i]['name'] == package_name, l))
	return ks[0]

def make_cache_graph(cache, no_python):
	g = networkx.DiGraph()
	for k in cache.keys():
		n = cache[k]['name']
		v = cache[k]['version']
		# Removing python to avoid cycles (--tree option)
		if no_python and n == "python": continue
		g.add_node(n, version=v)
		for j in cache[k]['depends']:
			n2 = j.split(' ')[0]
			v2 = j.split(' ')[1:]
			g.add_edge(n, n2, version=v2)
	return(g)

def print_graph_dot(g):
	print("digraph {")
	for k,v in g.edges():
	   print("  \"{}\" -> \"{}\"".format(k,v))
	print("}")

def remove_from_graph(g, node, _cache=None):
	if _cache is None: _cache = {}
	if node not in _cache:
		_cache[node] = True
		for k,v in g.out_edges(node):
			g = remove_from_graph(g, v, _cache)
	if node in g: g.remove_node(node)
	return(g)

def print_dependencies(g, pkg, parent, indent, args, treated, down_search):
	s = "" # String to print
	v = g.nodes[pkg]['version']
	edges = g.out_edges(pkg) if down_search else g.in_edges(pkg)
	e = [i[1] for i in edges] if down_search else [i[0] for i in edges]
	# Removing python to avoid cycles
	if "python" in e: e.remove("python")
	if args.no_conda and "conda" in e: e.remove("conda")
	if indent == 0:
		s += f"{pkg}=={v}\n"
	else:
		r = (', '.join(g.edges[parent, pkg]['version']) if down_search
		     else ', '.join(g.edges[pkg, parent]['version']))
		r = 'Any' if r == '' else r
		i_str = '  ' * indent
		s += f"{i_str}- {pkg} [required: {r}, installed: {v}]\n"
		if pkg in treated and not args.full:
			s += f"{i_str}  ... (already above)\n"
			return s, treated
		else:
			if len(e) > 0: treated.add(pkg)
	for pack in e: 
		tree_str, treat = print_dependencies(
			g, pack, pkg, indent+1, args, treated, down_search)
		s += tree_str
		for pkg_name in treat: treated.add(pkg_name)
	return s, treated

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-p','--prefix', default=None)
	parser.add_argument('-n','--name', default=None)
	parser.add_argument('-v','--version', action='version', version='%(prog)s '+__version__)

	subparser = parser.add_subparsers(dest='subcmd')
	subparser.add_parser('leaves', help='shows leaf packages')
	subparser.add_parser('cycles', help='shows dependency cycles')

	package_cmds = argparse.ArgumentParser(add_help=False)
	package_cmds.add_argument('package', help='the target package')

	rec_or_tree = package_cmds.add_mutually_exclusive_group(required=False)
	rec_or_tree.add_argument('-t', '--tree', help='show dependencies of dependencies in tree form, ignores python as a dependency to avoid cycles', default=False, action="store_true")
	rec_or_tree.add_argument('-r','--recursive', help='show dependencies of dependencies',default=False, action='store_true')

	hiding_cmds = argparse.ArgumentParser(add_help=False)
	hiding_cmds.add_argument('--no-conda', help='does not show dependencies of conda to make the tree easier to understand', default=False, action='store_true')
	hiding_cmds.add_argument('--full', help='shows the complete dependency tree, with all the repetitions that it entails', default=False, action='store_true')

	subparser.add_parser('whoneeds', help='shows packages that depends on this package', parents=[package_cmds, hiding_cmds])
	subparser.add_parser('depends', help='shows this package dependencies', parents=[package_cmds, hiding_cmds])
	subparser.add_parser('deptree', help="shows the complete dependency tree ('python' is excluded to avoid cycles)", parents=[hiding_cmds])

	args = parser.parse_args()

	if args.name is not None:
		# Allow user to specify name, but check the environment for an
		# existing CONDA_EXE command.  This allows a different conda
		# package to be installed (and imported above) but will
		# resolve the name using their expected conda.  (The imported
		# conda here will find the environments, but might not name
		# them as the user expects.)
		_conda = os.environ.get('CONDA_EXE', 'conda')
		_info = json.loads(subprocess.check_output(
			[_conda, 'info', '-e', '--json']))
		args.prefix = conda.base.context.locate_prefix_by_name(
			name=args.name, envs_dirs=_info['envs_dirs'])

	if args.prefix is None:
		args.prefix = sys.prefix
		 
	l = get_local_cache(args.prefix)
	no_python = True if (args.subcmd == "deptree" or args.tree) else False
	g = make_cache_graph(l, no_python)

	def get_leaves(graph):
		return list(map(lambda i:i[0],(filter(lambda i:i[1]==0,graph.in_degree()))))

	if args.subcmd == 'cycles':
		for i in networkx.simple_cycles(g):
			print(" -> ".join(i)+" -> "+i[0])

	elif args.subcmd == 'depends':
		if args.package not in g:
			print("warning: package \"%s\" not found"%(args.package), file=sys.stderr)
		if args.recursive:
			e = list(networkx.descendants(g, args.package))
			print(e)
		elif args.tree:
			if networkx.is_directed_acyclic_graph(g):
				tree, _ = print_dependencies(
					g, args.package, None, 0, args, set(), True)
				print(tree)
		else:
			e = list(map(lambda i: i[1], g.out_edges(args.package)))
			print(e)

	elif args.subcmd == 'whoneeds':
		if args.package not in g:
			print("warning: package \"%s\" not found"%(args.package), file=sys.stderr)
		if args.recursive:
			e = list(networkx.ancestors(g, args.package))
			print(e)
		elif args.tree:
			if networkx.is_directed_acyclic_graph(g):
				tree, _ = print_dependencies(
					g, args.package, None, 0, args, set(), False)
				print(tree)
		else:
			e = list(map(lambda i: i[0], g.in_edges(args.package)))
			print(e)

	elif args.subcmd == 'leaves':
		print(get_leaves(g))

	elif args.subcmd == 'deptree':
		treated = set()
		complete_tree = ""
		for pk in get_leaves(g):
			tree, treated = print_dependencies(g, pk, None, 0, args, treated)
			complete_tree += tree
		print(''.join(complete_tree))
	else:
		parser.print_help()
		sys.exit(1)

if __name__ == "__main__":
	main()

