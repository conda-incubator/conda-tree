
# conda-tree

conda dependency tree helper

# Usage

```bash
# packages that no other package depends on
$ ./conda-tree.py leafs
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
$ ./conda-tree.py -p /conda/envs/trinity leafs
['trinity']
```
