#!/usr/bin/env python
from __future__ import print_function
import argparse
import json
import os
import sys
import subprocess
import colorama
from colorama import Fore, Back, Style
colorama.init()

import conda.exports
import conda.api
import networkx

__version__ = '1.0.4'

# The number of spaces
TABSIZE = 3

def get_local_cache(prefix):
    return conda.exports.linked_data(prefix=prefix)

def get_package_key(cache, package_name):
    ks = list(filter(lambda i: cache[i]['name'] == package_name, cache))
    return ks[0]

def make_cache_graph(cache):
    g = networkx.DiGraph()
    for k in cache.keys():
        n = cache[k]['name']
        v = cache[k]['version']
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

def print_dep_tree(g, pkg, prev, state):
    # Unpack the state data
    down_search, args = state["down_search"], state["args"]
    indent = state["indent"]
    empty_cols, is_last = state["empty_cols"], state["is_last"]
    tree_exists = state["tree_exists"]

    s = ""                          # String to print
    v = g.nodes[pkg].get('version') # Version of package

    full_tree = True if ((hasattr(args, "full") and args.full)) else False

    # Create list of edges
    edges = g.out_edges(pkg) if down_search else g.in_edges(pkg)
    e = [i[1] for i in edges] if down_search else [i[0] for i in edges]
    # Maybe?: Sort edges in alphabetical order
    # e = sorted(e, key=(lambda i: i[1] if down_search else i[0]))

    if args.small:
        if "conda" in e: state["tree_exists"].add("conda")
        if "python" in e: state["tree_exists"].add("python")

    dependencies_to_hide = (True # We hide dependencies if...
        if ((pkg in state["tree_exists"] and not args.full)
            # Package already displayed and '--full' not used.
            or (args.full and pkg in state["tree_exists"] and pkg in state['pkgs_with_cycles']))
            # or, if '--full' is used but the package is part of a cyclic sub-graph
        else False)
    will_create_subtree = (True if len(e) >= 1 else False)
    if len(e) > 0: state["tree_exists"].add(pkg)

    # If the package is a leaf
    if indent == 0:
        if v is not None:
            s += f"{pkg}=={v}\n"
        else:
            s += pkg
    # Let's print the branch
    else:
        # Finding requirements for package from the parent
        # (or child, if we are running the 'whoneeds' subcommand)
        requirement = (', '.join(g.edges[prev, pkg]['version'])
            if down_search else ', '.join(g.edges[pkg, prev]['version']))
        r = 'any' if requirement == '' else requirement
        # Preparing the prepend string
        br = ('└─' if is_last else '├─')
        # Optional: + ('┬' if will_create_subtree else '─')
        i = ""
        for x in range(indent):
            if x == 0:
                i += ' ' * 2
            elif x in empty_cols:
                i += ' ' * TABSIZE
            else:
                i += ('│' + (' ' * (TABSIZE - 1)))
        if v is not None:
            s += f"{i}{br} {pkg}{Style.DIM} {v} [required: {r}]{Style.RESET_ALL}\n"
        else:
            s += f"{i}{br} {pkg}{Style.DIM} [required: {r}]{Style.RESET_ALL}\n"
        if dependencies_to_hide:
            state["hidden_dependencies"] = True
            will_create_subtree = False
            # We do not print these lines if:
            # python and conda dependencies if '-small' on
            if (pkg in ["python", "conda"] and args.small):
                pass
            else:
                br2 = ' ' if is_last else '│'
                word = "dependencies" if down_search else "dependent packages"
                s += f"{i}{br2}  {Style.DIM}└─ {word} of {pkg} displayed above{Style.RESET_ALL}\n"
        else:
            if len(e) > 0: state["tree_exists"].add(pkg)

    # Print the children
    if will_create_subtree:
        state["indent"] += 1
        for pack in e:
            if state["is_last"]: state["empty_cols"].append(indent)
            state["is_last"] = False if e[-1] != pack else True
            tree_str, state = print_dep_tree(g, pack, pkg, state)
            s += tree_str
    # If this is the last of its subtree to be printed
    if is_last and indent != 0:
        state["indent"] -= 1
        if indent in empty_cols: state["empty_cols"].remove(indent)
        state["is_last"] = False
    return s, state

def get_pkg_files(prefix):
    pkg_files = set()
    for p in conda.api.PrefixData(prefix).iter_records():
        for f in p['files']:
            pkg_files.add(f)
    return pkg_files

# check if dir is internal of conda
def is_internal_dir(prefix,path):
    for t in ['pkgs','conda-bld','conda-meta','locks','envs']:
        if path.startswith(os.path.join(prefix,t)): return True
    return False

def find_who_owns_file(prefix, target_path):
    for p in conda.api.PrefixData(prefix).iter_records():
        for f in p['files']:
            if target_path in f or f in target_path:
                print(p['name'], f)

def find_unowned_files(prefix):
    pkg_files = get_pkg_files(prefix)

    for root, dirs, files in os.walk(prefix):
        if is_internal_dir(prefix,root):
            continue

        for f in files:
            f0 = os.path.join(root,f)
            f1 = f0.replace(prefix, "", 1).lstrip(os.sep)
            if f1 not in pkg_files:
                print(f0)

def is_node_reachable(graph, source, target):
    if isinstance(source, list):
        for s in source:
            if is_node_reachable(graph, s, target):
                return True
    else:
        return any(networkx.algorithms.simple_paths.all_simple_paths(graph, source, target))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--prefix', default=None)
    parser.add_argument('-n','--name', default=None)
    parser.add_argument('-V','--version', action='version', version='%(prog)s '+__version__)

    subparser = parser.add_subparsers(dest='subcmd')

    # Arguments for "package_cmds" commands
    # Subcommands that deal with the dependencies of packages
    package_cmds = argparse.ArgumentParser(add_help=False)
    package_cmds.add_argument('package', help='the target package')

    # Arguments for "rec_or_tree" commands
    # Subcommands that can yield direct dependencies, recursive dependencies, or a tree view
    rec_or_tree = package_cmds.add_mutually_exclusive_group(required=False)
    rec_or_tree.add_argument('-t', '--tree',
        help=('show dependencies of dependencies in tree form'),
        default=False, action="store_true")
    rec_or_tree.add_argument('-r','--recursive',
        help='show dependencies of dependencies',
        default=False, action='store_true')

    # Arguments for "hiding" commands
    # Subcommands that enable users to hide a part of the result
    hiding_cmds = argparse.ArgumentParser(add_help=False)
    hiding_args = hiding_cmds.add_mutually_exclusive_group(required=False)
    hiding_args.add_argument('--small',
        help=('does not show dependencies of conda or python ' +
              'to make the tree easier to understand'),
        default=False, action='store_true')
    hiding_args.add_argument('--full',
        help=('shows the complete dependency tree,' +
              'with all the redundancies that it entails'),
        default=False, action='store_true')
    hiding_args.add_argument('--dot',
         help=('print a graphviz dot graph notation'), action='store_true', default=False)

    # Definining the simple subcommands
    lv_cmd = subparser.add_parser('leaves',
         help='shows leaf packages')
    lv_cmd.add_argument('--export', help='export leaves dependencies',
        action='store_true', default=False)
    lv_cmd.add_argument('--with-cycles', help='include orphan cycles',
        action='store_true', default=False)

    subparser.add_parser('cycles', help='shows dependency cycles')

    # Defining the complex subcommands
    subparser.add_parser('whoneeds',
        help='shows packages that depends on this package',
        parents=[package_cmds, hiding_cmds])
    subparser.add_parser('depends',
        help='shows this package dependencies',
        parents=[package_cmds, hiding_cmds])
    subparser.add_parser('deptree',
        help="shows the complete dependency tree",
        parents=[hiding_cmds])
    subparser.add_parser('unowned-files',
        help='shows files that are not owned by any package')
    subparser.add_parser('who-owns',
        help='find which package owns a given file').add_argument('file',help='a file path or substring of the target file')

    args = parser.parse_args()

    # Allow user to specify name, but check the environment for an
    # existing CONDA_EXE command.  This allows a different conda
    # package to be installed (and imported above) but will
    # resolve the name using their expected conda.  (The imported
    # conda here will find the environments, but might not name
    # them as the user expects.)
    if args.prefix is None:
        _conda = os.environ.get('CONDA_EXE', 'conda')
        _info = json.loads(subprocess.check_output(
            [_conda, 'info', '-e', '--json']))
        if args.name is None:
            if _info['active_prefix'] is not None:
                args.prefix = _info['active_prefix']
            else:
                args.prefix = _info['default_prefix']
        else:
            args.prefix = conda.base.context.locate_prefix_by_name(
                name=args.name, envs_dirs=_info['envs_dirs'])

    l = get_local_cache(args.prefix)
    g = make_cache_graph(l)

    ######
    # Helper functions for subcommands
    ######
    def get_leaves(graph):
        return list(map(lambda i:i[0],(filter(lambda i:i[1]==0,graph.in_degree()))))

    def get_leaves_plus_cycles(graph):
        lv = get_leaves(graph)
        for pks in networkx.simple_cycles(g):
            if is_node_reachable(g, lv, pks[0]):
                    pass
            else:
                 lv.append(pks[0])
        return lv

    def get_cycles(graph):
        s = ""
        for i in networkx.simple_cycles(graph):
            s += " -> ".join(i)+" -> "+i[0] + "\n"
        return s

    def pkgs_with_cycles(graph):
        return set(sum(networkx.simple_cycles(graph), []))

    # Default state for the recursive tree function
    state = {'down_search': True, 'args': args, 'indent': 0, 'indent': 0,
             'empty_cols': [], 'is_last': False, 'tree_exists': set(),
             'hidden_dependencies': False, 'pkgs_with_cycles': pkgs_with_cycles(g)}

    if args.subcmd == 'cycles':
        print(get_cycles(g), end='')

    elif args.subcmd in ['depends', 'whoneeds']:
        # This variable defines whether we are searching down the dependency
        # tree, or if rather we are looking for which packages depend on the
        # package, which would be searching up.
        # The 'depends' subcommand corresponds to a down search.
        state["down_search"] = (args.subcmd == "depends")
        if args.package not in g:
            print("warning: package \"%s\" not found"%(args.package), file=sys.stderr)
            sys.exit(1)
        if args.recursive:
            fn = networkx.descendants if state["down_search"] else networkx.ancestors
            e = list(fn(g, args.package))
            print(e)
        elif args.tree:
            tree, state = print_dep_tree(g, args.package, None, state)
            print(tree, end='')
        elif args.dot:
            fn = networkx.descendants if state["down_search"] else networkx.ancestors
            e = list(fn(g, args.package))
            print_graph_dot(g.subgraph(e+[args.package]))
        else:
            edges = g.out_edges(args.package) if state["down_search"] else g.in_edges(args.package)
            e = [i[1] for i in edges] if state["down_search"] else [i[0] for i in edges]
            print(e)

    elif args.subcmd == 'leaves':
        if args.with_cycles:
            lv = get_leaves_plus_cycles(g)
        else:
            lv = get_leaves(g)
        if args.export:
            for p in lv:
                k = get_package_key(l, p)
                print('%s::%s=%s=%s' % (l[k].channel.channel_name, l[k].name, l[k].version, l[k].build))
        else:
            print(lv)

    elif args.subcmd == 'deptree':
        if args.dot:
            print_graph_dot(g)
        else:
            complete_tree = ""
            for pk in get_leaves_plus_cycles(g):
                tree, state = print_dep_tree(g, pk, None, state)
                complete_tree += tree
            print(''.join(complete_tree), end='')

    elif args.subcmd == 'unowned-files':
        find_unowned_files(args.prefix)

    elif args.subcmd == 'who-owns':
        find_who_owns_file(args.prefix,args.file)

    else:
        parser.print_help()
        sys.exit(1)

    #######
    # End warning messages
    #######

    # If we use a tree-based command without --full enabled
    if state["hidden_dependencies"] and not args.full:
        print(f"\n{Style.DIM}For the sake of clarity, some redundancies have been hidden.\n" +
              f"Please use the '--full' option to display them anyway.{Style.RESET_ALL}")
        if not args.small:
            print(f"\n{Style.DIM}If you are tired of seeing 'conda' and 'python' everywhere,\n" +
              f"you can use the '--small' option to hide their dependencies completely.{Style.RESET_ALL}")

    # If we use a tree-based command without --full enabled
    if state["hidden_dependencies"] and args.full:
        print(f"\n{Style.DIM}The full dependency tree shows dependencies of packages " +
              f"with cycles only once.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()

