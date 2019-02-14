# Moonlite

A light-weight version of Moonbeam that uses AFL's internal tuples to generate
bitvectors for processing by Moonshine.

## Usage

```console
python moonlite.py -i <IN_DIR> -o <OUT_DIR> [--input-prefix <IN_PREFIX>] [--output-prefix <OUT_PREFIX> ] [--show-progress]
```

Where:

 * `IN_DIR` is the input directory containing all of the AFL tuples;
 * `OUT_DIR` is the output directory where the bitvectors will be written to;
 * `IN_PREFIX` is the prefix used by the input files that will be convereted to
   a bitvector file. The default is `afltuples-`;
 * `OUT_PREFIX` is the prefix used by the output bitvector files. The default
   is `examplar-`; and
 * `--show-progress` will show the current progress.
    
The input files are generated using `afl-showmap` on each seed file, e.g.:

```bash
for f in <CORPUS_DIR>/*; do
    LD_LIBRARY_PATH=<LIB_PATH> afl-showmap -e -q -m 800 -o <TARGET_DIR>/afltuples-$(basename ${f}) <PUT> <PUT_PARAMS>
done
```

Where:
 * `-m` specifies the memory limit;
 * `-e` ignores the tuple hit count (Moonshine does not require it);
 * `-q` suppresses program output;
 * `-o` specifies the output path/file name. In the above example, the prefix
   `afltuples-` will be used;
 * `<PUT>` is the program under test (PUT); and
 * `<PUT_PARAMS>` are any arguments that the may take.

Additionally, the tuples are also a byproduct of running `afl-cmin`. Specify
the environment variable `AFL_KEEP_TRACES=1` and the tuples will be located
inside the directory `<CMIN_RESULT>/*.traces` along with other CMIN
intermediary results.
