
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
$ conda-tree depends sqlite
sqlite==3.29.0
  - ncurses [required: >=6.1,<6.2.0a0, installed: 6.1]
    - libcxx [required: >=4.0.1, installed: 8.0.1]
      - libcxxabi [required: 8.0.1, 0, installed: 8.0.1]
  - readline [required: >=8.0,<9.0a0, installed: 8.0]
    - ncurses [required: >=6.1,<6.2.0a0, installed: 6.1]
      ... (already above)

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
  - pynvim [required: Any, installed: 0.3.2]
    - greenlet [required: Any, installed: 0.4.15]
    - msgpack-python [required: >=0.5.0, installed: 0.6.1]
      - libcxx [required: >=4.0.1, installed: 8.0.1]
        - libcxxabi [required: 8.0.1, 0, installed: 8.0.1]
conda-tree==0.0.4
  - conda [required: Any, installed: 4.7.11]
    - conda-package-handling [required: >=1.3.0, installed: 1.4.1]
      - libarchive [required: >=3.3.3, installed: 3.3.3]
...

# query a different conda prefix/env
$ conda-tree -p /conda/envs/trinity leaves
['trinity']

# query by name
$ conda-tree -n trinity leaves
['trinity']
```
