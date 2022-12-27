
## conda-tree

conda dependency tree helper

## Install

```bash
conda install -c conda-forge conda-tree
```
  
  
If you're using python 3.9 you might have to run:
```bash
conda install -c conda-forge conda-tree 'networkx>=2.5'
```
to make sure the right networkx version is installed.

## Conda sub-command

When conda-tree is installed on the base environment, you can use the "tree" sub-command from any env:

```bash
# normal usage
(base) $ conda tree leaves
package-1
package-2

# activate another env
(base) $ conda activate env2

# no need to install conda-tree on env2
(env2) $ conda tree leaves
package-x
package-y
```

## Features

### Query the dependency tree

```bash
# packages that no other package depends on
$ conda-tree leaves
samtools
bcftools
etc

# dependencies of a specific package
$ conda-tree depends samtools
curl
xz
libgcc
zlib

# which packages depend on a specific package
$ conda-tree whoneeds xz
samtools
bcftools
htslib
python

# dependency cycles
$ conda-tree cycles
pip -> python -> pip
pip -> wheel -> python -> pip
```

### Dependencies in tree form

```bash
# dependencies in a tree form
# (redundancies are hidden by default)
$ conda-tree depends -t sqlite
sqlite==3.29.0
  ├─ ncurses 6.1 [required: >=6.1,<6.2.0a0]
  │  └─ libcxx 8.0.1 [required: >=4.0.1]
  │     └─ libcxxabi 8.0.1 [required: 8.0.1, 0]
  └─ readline 8.0 [required: >=8.0,<9.0a0]
     └─ ncurses 6.1 [required: >=6.1,<6.2.0a0]
        └─ dependencies of ncurses displayed above

# full dependency tree
$ conda-tree deptree --full
neovim==0.3.1
  ├─ pynvim 0.3.2 [required: any]
  │  ├─ greenlet 0.4.15 [required: any]
  │  │  └─ python 3.7.3 [required: >=3.7,<3.8.0a0]
  │  │     ├─ bzip2 1.0.8 [required: >=1.0.6,<2.0a0]
  │  │     ├─ libcxx 8.0.1 [required: >=4.0.1]
  │  │     │  └─ libcxxabi 8.0.1 [required: 8.0.1, 0]
  │  │     ├─ libffi 3.2.1 [required: >=3.2.1,<3.3.0a0]
...
conda-tree==0.0.4
  ├─ conda 4.7.11 [required: any]
  │  ├─ conda-package-handling 1.4.1 [required: >=1.3.0]
  │  │  ├─ libarchive 3.3.3 [required: >=3.3.3]
  │  │  │  ├─ bzip2 1.0.8 [required: >=1.0.6,<2.0a0]
...
```

### Query another env

```bash
# query by path
$ conda-tree -p /conda/envs/trinity leaves
trinity

# query by name
$ conda-tree -n trinity leaves
trinity
```

### Query package files

```bash
# find which package owns a file
$ conda-tree -n graphviz who-owns bin/dot
graphviz bin/dot
graphviz bin/dot2gxl
graphviz bin/dot_builtins

# find dangling files that aren't owned by any package
$ conda-tree -n base unowned-files
/conda/LICENSE.txt

$ conda-tree -n graphviz unowned-files
/conda/envs/graphviz/var/cache/fontconfig/b67b32625a2bb51b023d3814a918f351-le64.cache-7
/conda/envs/graphviz/var/cache/fontconfig/f93dd067-84cf-499d-a5a8-645ff5f927dc-le64.cache-7
/conda/envs/graphviz/var/cache/fontconfig/923e285e415b1073c8df160bee08820f-le64.cache-7
/conda/envs/graphviz/fonts/.uuid
```

### Generate a minimal set of packages to re-create the env

```bash
# can be used to re-create a env with conda create -n <new-env> --file <dep-file>
$ conda-tree -n graphviz leaves --export
conda-forge::graphviz=2.48.0=h85b4f2f_0
```

### Generate a graph of the dependency tree

```bash
# export a graphviz dot notation file of the dependencies tree
$ conda-tree deptree --dot > file.dot
$ conda-tree depends <package> --dot > file.dot
$ conda-tree whoneeds <package> --dot > file.dot

# then render to pdf with graphviz's dot tool
$ dot -Tpdf file.dot -o tree.pdf

```
