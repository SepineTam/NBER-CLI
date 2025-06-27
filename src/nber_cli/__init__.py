import argparse
import asyncio
import os

from .core.download.downloader import main_download_multiple


def main():
    parser = argparse.ArgumentParser(description="Download NBER papers.")
    parser.add_argument(
        "-d",
        "-D",
        "--download",
        dest="paper_ids",
        required=True,
        nargs='+',
        type=str,
        help="One or more NBER paper IDs (e.g., w1234 w5678).")
    parser.add_argument(
        "--save_path",
        type=str,
        default=os.path.expanduser("~/Documents/nber_paper"),
        help="The directory to save the downloaded paper. Defaults to ~/Documents/nber_paper.")

    args = parser.parse_args()

    asyncio.run(main_download_multiple(args.paper_ids, args.save_path))
