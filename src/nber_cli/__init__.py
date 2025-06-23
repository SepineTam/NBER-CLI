import argparse
import asyncio
import os
from .downloader import main_download

def main():
    parser = argparse.ArgumentParser(description="Download NBER papers.")
    parser.add_argument("paper_id", type=str, help="The NBER paper ID (e.g., w1234).")
    parser.add_argument("--save_path", type=str, default=os.path.expanduser("~/Documents/nber_paper"),
                        help="The directory to save the downloaded paper. Defaults to ~/Documents/nber_paper.")

    args = parser.parse_args()

    asyncio.run(main_download(args.paper_id, args.save_path))


