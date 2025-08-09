import argparse
import asyncio
import os
import sys
from importlib.metadata import version as get_version

from .core.download.downloader import main_download_multiple


def get_version_info() -> str:
    """Get the version information of the package."""
    try:
        return get_version("nber-cli")
    except Exception:
        return "0.1.3"  # Fallback version


def main():
    parser = argparse.ArgumentParser(
        description="NBER CLI - A command-line tool to download NBER papers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nber-cli -d w1234 w5678
  nber-cli --download w1234 --save_path ./papers
  nber-cli --version
  nber-cli --help
        """
    )
    
    # 添加版本参数
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"NBER CLI v{get_version_info()}"
    )
    
    # 添加下载参数组
    download_group = parser.add_argument_group("Download Options")
    download_group.add_argument(
        "-d",
        "-D",
        "--download",
        dest="paper_ids",
        nargs='+',
        type=str,
        help="One or more NBER paper IDs (e.g., w1234 w5678).")
    download_group.add_argument(
        "--save_path",
        type=str,
        default=os.path.expanduser("~/Documents/nber_paper"),
        help="The directory to save the downloaded paper. Defaults to ~/Documents/nber_paper.")

    args = parser.parse_args()
    
    # 如果没有提供任何参数，显示帮助信息
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(0)
    
    # 如果提供了paper_ids参数，执行下载
    if args.paper_ids:
        asyncio.run(main_download_multiple(args.paper_ids, args.save_path))
    else:
        parser.print_help()
        sys.exit(1)
