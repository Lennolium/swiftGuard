#!/usr/bin/env python3

"""
hash.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2023-10-19"
__status__ = "Prototype/Development/Production"

# Imports.
import hashlib
import logging
import os

from swiftguard import const

# Child logger.
LOGGER = logging.getLogger(__name__)


# Credits to @BusKill on GitHub (see ACKNOWLEDGEMENTS).
def parse(sha256sums_filepath):
    # Parse the SHA256SUMS file and convert it into a dictionary.
    sha256sums = {}
    with open(sha256sums_filepath, "r") as fh:
        for line in fh:
            # SHA256 hashes are exactly 64 characters long.
            checksum = line[:64]

            # Two spaces between checksum and filename.
            file_path = line[66:].strip()

            sha256sums[file_path] = checksum

        LOGGER.debug(f"Successfully parsed SHA256SUMS: {sha256sums}")
        return sha256sums


# Will raise RuntimeError if at least one checksum does not match.
# Credits to @BusKill on GitHub (see ACKNOWLEDGEMENTS).
def check_integrity(local_files, hash_file):
    # Parse the SHA256SUMS file and convert it into a dictionary.
    sha256sums = parse(hash_file)

    # Loop through each file that we were asked to check and confirm
    # its checksum matches what was listed in the SHA256SUMS file.
    for local_file in local_files:
        sha256sum = hashlib.sha256()

        with open(os.path.join(const.APP_PATH, local_file), "rb") as fd:
            while data_chunk := fd.read(1024):
                sha256sum.update(data_chunk)

        checksum = sha256sum.hexdigest()

        LOGGER.debug(
                f"Local[{local_file}]: {checksum}\n"
                f"SHA256SUMS[{local_file}]: {sha256sums[local_file]}\n"
                )

        # If the checksums do not match, raise RuntimeError -> Integrity
        # check failed.
        if checksum != sha256sums[local_file]:
            msg = (
                    "INTEGRITY CHECK FAILED! Checksums of local file "
                    f"({local_file}) and SHA256SUMS do not match!\n"
                    f"{checksum} != {sha256sums[local_file]}\n"
                    "Please reinstall swiftGuard."
            )

            raise RuntimeError(msg)

    LOGGER.info("Integrity check passed.")
