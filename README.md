
# conda-tree

conda dependency tree helper

# Install

This helper requires only that `conda-tree.py` be on your path and
that the `conda` and `networkx` packages are installed.  This can be
done with `conda` itself if you like:

```bash
conda install -c rvalieris conda-tree
```

# Usage

```bash
# packages that no other package depends on
$ ./conda-tree.py leaves
['samtools','bcftools',...]

# dependencies of a specific package
$ ./conda-tree.py depends samtools
['curl', 'xz', 'libgcc', 'zlib']

# which packages depend on a specific package
$ ./conda-tree.py whoneeds xz
['samtools', 'bcftools', 'htslib', 'python']

# dependency cycles
$ ./conda-tree.py cycles
pip -> python -> pip
pip -> wheel -> python -> pip

# query a different conda prefix/env
$ ./conda-tree.py -p /conda/envs/trinity leaves
['trinity']

# query by name
$ ./conda-tree.py -n trinity leaves
['trinity']
```
