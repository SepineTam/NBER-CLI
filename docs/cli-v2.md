# NBER-CLI v0.2 Command Reference

## Download a single paper

```bash
nber-cli download w1234
```

Saves to `./w1234.pdf` by default (current working directory).

## Download a single paper to an explicit file

```bash
nber-cli download w1234 --file /path/to/save/w1234.pdf
nber-cli download w1234 -f /path/to/save/w1234.pdf
```

When `--file` is set, it always overrides `--save-base`.

## Download a single paper with a base directory

```bash
nber-cli download w1234 --save-base /path/to/save
nber-cli download w1234 -s /path/to/save
```

Result file path: `/path/to/save/w1234.pdf`.

## Batch download

```bash
nber-cli download --batch w1234 w23156 w1516 --save-base /path/to/save
nber-cli download -b w1235 w4568 w0485
```

Batch mode supports `--save-base` only.
Batch mode does not support `--file`.
