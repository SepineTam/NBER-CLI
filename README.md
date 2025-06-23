# NBER-CLI
NBER-CLI is a command line interface for the National Bureau of Economic Research (NBER) paper data.


## Installation
```bash
pip install nber-cli
```

or you can install it from github for the beta version:
```bash
pip install git+https://github.com/sepinetam/nber-cli.git
```

## Usage
```bash
nber-cli --help
```

- Download the certain paper to default directory:
```bash
nber-cli paper_id
```

- Download the certain paper to a specific directory:
```bash
nber-cli paper_id --save_path /path/to/directory
```

An example of downloading a paper with ID `w1234` to the specific directory:
```bash
(base) ~/Documents/Github/nber_cli git:[master]
nber-cli w1234 --save_path ~/Downloads/nber-cli
2025-06-23 12:00:29,266 - INFO - Loaded 1 ok ids and 0 fail ids from db.
2025-06-23 12:00:41,097 - INFO - Successfully downloaded w1234 to /Users/sepinetam/Downloads/nber-cli/w1234.pdf
```

## LICENSE
[APACHE-2.0](LICENSE)
