#!/usr/bin/env python3

"""
enc.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__date__ = "2023-10-19"
__status__ = "Prototype/Development/Production"

# Imports.
import configparser
import logging
import os.path
import secrets
import shutil

import keyring as kr
import requests

from swiftguard import const

# Child logger.
LOGGER = logging.getLogger(__name__)


def key_set_credentials(fp, passphrase):
    # Save fingerprint and passphrase in keyring.
    kr.set_password(
            f"swiftGuard-fp-v{__version__}",
            "swiftguard@lennolium.dev",
            str(fp),
            )

    kr.set_password(
            f"swiftGuard-key-v{__version__}",
            "swiftguard@lennolium.dev",
            str(passphrase),
            )


def key_get_credentials():
    # Check if passphrase for key and its fingerprint are stored in KR.
    if kr.get_credential(
            f"swiftGuard-key-v{__version__}", "swiftguard@lennolium.dev"
            ) and kr.get_credential(
            f"swiftGuard-fp-v{__version__}", "swiftguard@lennolium.dev"
            ):
        # Get fingerprint.
        fp = kr.get_password(
                f"swiftGuard-fp-v{__version__}", "swiftguard@lennolium.dev"
                )

        # Get passphrase.
        passphrase = kr.get_password(
                f"swiftGuard-key-v{__version__}", "swiftguard@lennolium.dev"
                )

        return fp, passphrase

    return None, None


def key_download(fp, key_filepath):
    # Create local directory for storing public key.
    os.makedirs(os.path.dirname(const.GPG_RELEASE_KEY), exist_ok=True)

    # Download public key from key server (keys.openpgp.org).
    url = f"{const.URLS['keyserver']}{fp}"
    try:
        with requests.get(url, stream=True, timeout=1) as rh:
            # Do not download any files bigger than 1 MB.
            file_size = int(rh.headers["Content-length"])
            if file_size > 1048576:
                raise RuntimeError(
                        "Downloaded public key file size is "
                        f"{file_size / 1048576} MB, but the size limit (1 MB)."
                        )

            # Write file to disk (overwrite shipped key).
            with open(key_filepath, "wb") as fh:
                shutil.copyfileobj(rh.raw, fh)

            LOGGER.debug(
                    "Successfully downloaded public key "
                    f"from {url} and wrote it to {key_filepath}."
                    )

    except Exception as e:
        if os.path.isfile(key_filepath):
            shutil.copyfile(const.GPG_INSTALL_KEY, key_filepath)
            LOGGER.error(
                    "Aborted download of public key from key server. "
                    f"Falling back to local copy. Error: {str(e)}."
                    )
        else:
            raise RuntimeError(
                    "Aborted download of public key from key server. "
                    f"Error: {str(e)}.\n"
                    f"No fallback (local copy at {const.GPG_INSTALL_KEY}) "
                    "found -> No integrity check possible."
                    ) from e


def key_import(fp, key_filepath):
    # Check if key is already imported.
    try:
        _ = const.GPG_STORE.list_keys().key_map[fp]["fingerprint"]
        LOGGER.info(f"Already imported key with fingerprint {fp}.")
        # TODO: remove!
        print("scchon drin")

        return

    # Not imported yet.
    except KeyError:
        pass

    # Import public key.
    imp = const.GPG_STORE.import_keys_file(key_filepath)
    if imp.count:
        print(f"Successfully imported key with fingerprint {fp}.")

    else:
        print("Failed to import key.")


def key_create() -> (str, str):
    LOGGER.debug(
            f"The GnuPG home directory is set to: {const.GPG_STORE.gnupghome}"
            )
    LOGGER.debug(f"The GnuPG executable is: {const.GPG_STORE.gpgbinary}")

    # Check if passphrase for key and its fingerprint are stored in KR.
    key_fp, passphrase = key_get_credentials()

    # If they exist, return them and do not create a new key.
    if key_fp and passphrase:
        print(f"Already exists a key with following fingerprint: {key_fp}.")
        return key_fp, passphrase

    # Not present in keyring -> generate random passphrase for key,
    # generate new key and store passphrase and fingerprint in keyring.
    passphrase = secrets.token_urlsafe(32)
    key_input = const.GPG_STORE.gen_key_input(
            key_type="RSA",
            key_length=4096,
            name_real="swiftGuard",
            name_email="swiftguard@lennolium.dev",
            name_comment="Signing and Encryption Key",
            passphrase=passphrase,
            )
    key_fp = const.GPG_STORE.gen_key(key_input)
    if key_fp.status != "ok":
        raise RuntimeError(
                f"Failed to create new key. Error: {str(key_fp.stderr)}"
                )

    print(f"Created new key with fingerprint: {str(key_fp)}.")

    # Save fingerprint and passphrase in keyring.
    key_set_credentials(key_fp, passphrase)

    return key_fp, passphrase


def sign(files):
    passphrase = kr.get_password(
            f"swiftGuard-key-v{__version__}", "swiftguard@lennolium.dev"
            )

    for i, file in enumerate(files):
        # Sign file.
        with open(file, "rb") as fh:
            stream = const.GPG_STORE.sign_file(
                    fh,
                    passphrase=passphrase,
                    detach=True,
                    output=f"{files[i]}.asc",
                    )

            print(f"{file} ", stream.status)


def verify(files: list) -> bool or RuntimeError:
    # Verify signature of files.
    for file in files:

        # Remove file extension if present.
        if file.endswith(".asc"):
            file = file[:-4]

        with open(f"{file}.asc", "rb") as fh:
            verify = const.GPG_STORE.verify_file(fh, file)
            # TODO: dont print, log instead.
            print(f"{file}:", verify.status)

            if not verify:
                raise RuntimeError(
                        f"Signature of checked file ({file}) is "
                        "invalid. Integrity of swiftGuard cannot "
                        "be guaranteed."
                        )

    return True


def encrypt(files: list) -> None:
    # Get fingerprint and passphrase from keyring.
    fp, passphrase = key_get_credentials()

    # Encrypt and sign files.
    for file in files:
        with open(file, "rb") as fh:
            data = const.GPG_STORE.encrypt_file(
                    fileobj_or_path=fh,
                    recipients=fp,
                    passphrase=passphrase,
                    sign=fp,
                    output=f"{file}.gpg"
                    )


def decrypt(files: list) -> None:
    # Get fingerprint and passphrase from keyring.
    fp, passphrase = key_get_credentials()

    # Decrypt and verify files.
    for file in files:
        with open(f"{file}.gpg", "rb") as fh:
            data = const.GPG_STORE.decrypt_file(
                    fileobj_or_path=fh,
                    passphrase=passphrase,
                    output=file,
                    )

            if data.fingerprint != fp:
                raise RuntimeError(
                        f"Fingerprints do not match ({file}). "
                        f"Decryption of file failed."
                        )


def convert_conf() -> None:
    # Get fingerprint and passphrase from keyring.
    fp, passphrase = key_get_credentials()

    # If no encrypted config is present ...
    if not os.path.isfile(f"{const.CONFIG_FILE}.gpg"):
        # ... encrypt and sign plain .ini config file -> .gpg file.
        with open(const.CONFIG_FILE, "rb") as fh:
            data = const.GPG_STORE.encrypt_file(
                    fileobj_or_path=fh,
                    recipients=fp,
                    passphrase=passphrase,
                    sign=fp,
                    always_trust=True,
                    output=f"{const.CONFIG_FILE}.gpg"
                    )

        # Delete plain .ini config file.
        os.remove(const.CONFIG_FILE)

    else:
        # Convert .gpg file to .ini file.
        with open(f"{const.CONFIG_FILE}.gpg", "rb") as fh:
            data = const.GPG_STORE.decrypt_file(
                    fileobj_or_path=fh,
                    passphrase=passphrase,
                    always_trust=True,
                    output=const.CONFIG_FILE,
                    )

            if data.fingerprint != fp:
                raise RuntimeError(
                        f"Fingerprints do not match ({const.CONFIG_FILE}). "
                        f"Conversion of GPG config file to .ini failed."
                        )

        # Delete .gpg config file.
        os.remove(f"{const.CONFIG_FILE}.gpg")


def encrypt_conf(config: configparser.ConfigParser):
    # Get fingerprint and passphrase from keyring.
    fp, passphrase = key_get_credentials()

    # Convert config object to string representation.
    parsed = ""
    for section in config.sections():
        parsed += f"[{section}]\n"
        for key, value in config.items(section):
            parsed += f"{key} = {value}\n"
        parsed += "\n"

    # Encrypt and sign config file.
    const.GPG_STORE.encrypt(
            parsed, fp,
            passphrase=passphrase,
            sign=fp,
            always_trust=True,
            output=f"{const.CONFIG_FILE}.gpg"
            )


def decrypt_conf(file: str) -> configparser.ConfigParser:
    # Get fingerprint and passphrase from keyring.
    fp, passphrase = key_get_credentials()

    # Remove file extension if present.
    if file.endswith(".gpg"):
        file = file[:-4]

    # Decrypt and verify config file.
    with open(f"{file}.gpg", "rb") as fh:
        data = const.GPG_STORE.decrypt(
                fh.read(),
                passphrase=passphrase,
                always_trust=True,
                )

        if data.fingerprint != fp:
            raise RuntimeError(
                    f"Fingerprints do not match ({file}). "
                    f"Integrity check of config file failed."
                    )

        parsed = data.data.decode("ascii", "ignore")

        config = configparser.ConfigParser(allow_no_value=True)
        config.read_string(parsed)

        # TODO: remove
        print(config.sections())
        print(config["Application"]["log"])

        return config


def main():
    import time
    from swiftguard.utils import conf
    start = time.perf_counter()

    # First try to download the public key from the key server.
    key_download(const.GPG_RELEASE_FP,
                 const.GPG_RELEASE_KEY
                 )

    # Import public key (downloaded or local fallback) into GPG keyring.
    key_import(
            const.GPG_RELEASE_FP, const.GPG_RELEASE_KEY
            )

    # Verify integrity of SHA256SUMS file.
    if verify([f"{const.APP_PATH}/install/SHA256SUMS"]):
        print("SHA256SUMS file is valid.")
    else:
        print("SHA256SUMS file is INVALID.")

    # Create new key for encryption and signing of config file.
    key_fp, key_pw = key_create()
    print("fp:", key_fp, "pw", key_pw)

    cfg = conf.load(configparser.ConfigParser())

    encrypt_conf(cfg)

    decrypt_conf(const.CONFIG_FILE)

    end = time.perf_counter()
    print(f"Finished in {(end - start):.2f} seconds.")


if __name__ == "__main__":
    main()
