
# conda-tree

conda dependency tree helper

# Install

This helper requires only that `conda-tree.py` be on your path and
that the `conda` and `networkx` packages are installed.  This can be
done with `conda` itself if you like:

```bash
conda install -c conda-forge conda-tree
```

# Usage

```bash
# packages that no other package depends on
$ conda-tree leaves
['samtools','bcftools',...]

# dependencies of a specific package
$ conda-tree depends samtools
['curl', 'xz', 'libgcc', 'zlib']

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

# which packages depend on a specific package
$ conda-tree whoneeds xz
['samtools', 'bcftools', 'htslib', 'python']

# dependency cycles
$ conda-tree cycles
pip -> python -> pip
pip -> wheel -> python -> pip

# full dependency tree
$ conda-tree deptree --full
neovim==0.3.1
   └─ pynvim 0.3.2 [required: any]
      ├─ greenlet 0.4.15 [required: any]
      └─ msgpack-python 0.6.1 [required: >=0.5.0]
         └─ libcxx 8.0.1 [required: >=4.0.1]
            └─ libcxxabi 8.0.1 [required: 8.0.1, 0]
conda-tree==0.0.4
   ├─ conda 4.7.11 [required: any]
   │  ├─ conda-package-handling 1.4.1 [required: >=1.3.0]
   │  │  ├─ libarchive 3.3.3 [required: >=3.3.3]
...

# query a different conda prefix/env
$ conda-tree -p /conda/envs/trinity leaves
['trinity']

# query by name
$ conda-tree -n trinity leaves
['trinity']
```
