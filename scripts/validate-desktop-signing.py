from __future__ import annotations

import argparse
import os
import sys


MACOS_REQUIRED = (
    "APPLE_CERTIFICATE",
    "APPLE_CERTIFICATE_PASSWORD",
    "KEYCHAIN_PASSWORD",
    "APPLE_ID",
    "APPLE_PASSWORD",
    "APPLE_TEAM_ID",
)
WINDOWS_REQUIRED = (
    "WINDOWS_CERTIFICATE",
    "WINDOWS_CERTIFICATE_PASSWORD",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate desktop release signing environment.")
    parser.add_argument("--platform", choices=["macos", "windows"], required=True)
    parser.add_argument("--require-signed", action="store_true")
    args = parser.parse_args()

    missing = missing_signing_variables(args.platform)
    if missing:
        for name in missing:
            print(f"{name} is required for signed {args.platform} desktop releases.")
        if args.require_signed:
            raise SystemExit(1)
        print(f"{args.platform}_signing=not_configured")
        return

    print(f"{args.platform}_signing=configured")


def missing_signing_variables(platform_name: str) -> list[str]:
    required = MACOS_REQUIRED if platform_name == "macos" else WINDOWS_REQUIRED
    return [name for name in required if not os.environ.get(name)]


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
