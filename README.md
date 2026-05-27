# NBER-CLI

NBER-CLI is a command line tool for downloading NBER paper PDFs.

## Installation

```bash
pip install nber-cli
```

## CLI v0.2 Usage

```bash
nber-cli download w1234
nber-cli download w1234 --file /path/to/save/w1234.pdf
nber-cli download w1234 -f /path/to/save/w1234.pdf
nber-cli download w1234 --save-base /path/to/save
nber-cli download w1234 -s /path/to/save
nber-cli download --batch w1234 w23156 w1516 --save-base /path/to/save
nber-cli download -b w1235 w4568 w0485
```

Rules:

- If neither `--file` nor `--save-base` is set, files are saved to `Path.cwd()`.
- If both `--file` and `--save-base` are set, `--file` wins.
- Batch download supports `--save-base` only.
- Batch download does not support `--file`.


## License

[Apache-2.0](LICENSE)
