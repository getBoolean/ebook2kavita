"""
Script to convert an eBook folder structure to a Kavita folder structure.
"""

import os
import time
import sys
import shutil
import argparse
import re
import subprocess
import tempfile
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Literal

from tqdm import tqdm


# ************************************************************ #
# ***************** START OF EBOOK META UTILS ***************** #
# ************************************************************ #


VOLUME_PATTERNS: list[re.Pattern] = [
    re.compile(r"v[\s.-]*(\d+(\.\d+)?)", re.IGNORECASE),
    re.compile(r"vol[\s.-]*(\d+(\.\d+)?)", re.IGNORECASE),
    re.compile(r"volume[\s.-]*(\d+(\.\d+)?)", re.IGNORECASE),
    re.compile(r"LN[\s]*(\d+(\.\d+)?)", re.IGNORECASE),
]

BACKUP_VOLUME_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")

PART_PATTERNS: list[re.Pattern] = [
    re.compile(r"part[\s.-]*(\d+(\.\d+)?)", re.IGNORECASE),
    re.compile(r"pt[\s.-]*(\d+(\.\d+)?)", re.IGNORECASE),
]

YEAR_PATTERNS: list[re.Pattern] = [
    re.compile(r"year[\s.-]*(\d+(\.\d+)?)", re.IGNORECASE),
]

SIDESTORY_PATTERNS: list[re.Pattern] = [
    re.compile(r"ss[\s.-]*(\d+(\.\d+)?)", re.IGNORECASE),
    re.compile(r"extra[\s.-]*(\d+(\.\d+)?)", re.IGNORECASE),
    re.compile(r"special[\s.-]*(\d+(\.\d+)?)", re.IGNORECASE),
]


def is_locked(filepath: str) -> bool | None:
    """Checks if a file is locked by opening it in append mode.
    If no exception thrown, then the file is not locked.

    Source: https://www.calazan.com/how-to-check-if-a-file-is-locked-in-python/
    """
    locked = None
    file_object = None
    if os.path.exists(filepath):
        try:
            buffer_size = 8
            # Opening file in append mode and read the first 8 characters.
            file_object = open(filepath, "a", buffer_size, encoding="utf-8")
            if file_object:
                locked = False
        except IOError:
            locked = True
        finally:
            if file_object:
                file_object.close()
    return locked


def convert_and_fix_ebook(
    src_ebook_file_path: str, target_epub_path: str, dont_split_on_page_breaks: bool
) -> None:
    """
    Convert a given eBook file, convert it to EPUB format, and fix any issues.

    This also runs Calibre plugin [DeDRM](https://github.com/noDRM/DeDRM_tools)
    if it is installed.
    """
    if not shutil.which("ebook-convert"):
        print(
            "Error: Calibre's ebook-convert not found in the path. "
            + "Please install Calibre and add the installation directory to the PATH.",
            file=sys.stderr,
        )
        sys.exit(1)

    command = ["ebook-convert", src_ebook_file_path, target_epub_path]
    command += ["--no-default-epub-cover", "--no-svg-cover"]
    if dont_split_on_page_breaks:
        command += ["--dont-split-on-page-breaks"]
    while is_locked(src_ebook_file_path):
        time.sleep(0.5)
    result = subprocess.run(command, shell=True, capture_output=True, check=False)

    if result.returncode != 0:
        print("Error:", result.stderr.decode("utf-8"), file=sys.stderr)


def set_epub_series_and_index(
    target_epub_file_path: str,
    series_title: str,
    series_year_num: str | None,
    series_part_num: str | None,
    volume_num: str | None,
    volume_part_num: str | None,
    folder_index: int,
) -> None:
    """
    Set the series and index of an eBook file using calibre.
    """
    title: str = series_title
    if series_year_num:
        title += f" Year {series_year_num}"

    if series_part_num:
        title += f" Part {series_part_num}"

    if not shutil.which("ebook-meta"):
        print(
            "Error: Calibre's ebook-meta not found in the path. "
            + "Please install Calibre and add the installation directory to the PATH.",
            file=sys.stderr,
        )
        sys.exit(1)

    command = ["ebook-meta", target_epub_file_path, "--series", title]

    if volume_num is not None:
        index = volume_num
        if volume_part_num:
            index += f"{volume_num}.{volume_part_num}"
        command += ["--index", index]
    else:
        index = f"1.{folder_index}"
        command += ["--index", index]

    while is_locked(target_epub_file_path):
        time.sleep(0.5)
    result = subprocess.run(command, shell=True, capture_output=True, check=False)

    # Check the output for errors
    if result.returncode != 0:
        print("Error:", result.stderr.decode("utf-8"), file=sys.stderr)


def extract_series_year_number(filename: str) -> str | None:
    """
    Extract the part number from the filename.
    """
    return extract_part_pattern(filename, YEAR_PATTERNS, part_type="series")


def extract_series_part_number(filename: str) -> str | None:
    """
    Extract the part number from the filename.
    """
    return extract_part_pattern(filename, PART_PATTERNS, part_type="series")


def extract_volume_part_number(filename: str) -> str | None:
    """
    Extract the part number from the filename.

    Note that this won't work for files with both series parts and volume parts
    such as `Title Part 2 - Volume 1 Part 2`. It will (likely) return None.
    """
    return extract_part_pattern(filename, PART_PATTERNS, part_type="volume")


def extract_part_pattern(
    filename: str, patterns: list[re.Pattern], part_type: Literal["series", "volume"]
) -> str | None:
    """
    Extract the part number from the filename.

    Note that volume won't work for files with both series parts and volume parts
    such as `Title Part 2 - Volume 1 Part 2`. It will (likely) return None.
    """

    for pattern in patterns:
        match = pattern.search(filename)
        if match:
            # Check that series part pattern must come after VOLUME_PATTERNS
            for volume_pattern in VOLUME_PATTERNS:
                volume_matches = matches_pattern(
                    filename, match, volume_pattern, part_type
                )
                if volume_matches:
                    return None

            for volume_pattern in SIDESTORY_PATTERNS:
                volume_matches = matches_pattern(
                    filename, match, volume_pattern, part_type
                )
                if volume_matches:
                    return None

            try:
                return match.group(1)
            except IndexError:
                return match.group(0)

    return None


def matches_pattern(
    filename: str,
    match: re.Match[str],
    pattern: re.Pattern,
    part_type: Literal["series", "volume"],
) -> bool:
    """
    Check if the given filename matches the given pattern.
    """
    volume_match = pattern.search(filename)
    if volume_match and (
        (part_type == "volume" and volume_match.start() > match.start())
        or (part_type == "series" and volume_match.start() < match.start())
    ):
        return True
    return False


def extract_volume_number(filename: str) -> str | None:
    """
    Extract the volume number from the filename.
    """

    for pattern in VOLUME_PATTERNS:
        match = pattern.search(filename)
        if match:
            try:
                return match.group(1)
            except IndexError:
                return match.group(0)

    for pattern in SIDESTORY_PATTERNS:
        match = pattern.search(filename)
        if match:
            try:
                return match.group(1)
            except IndexError:
                return match.group(0)

    if not extract_series_part_number(filename):
        match = BACKUP_VOLUME_PATTERN.search(filename)
        if match:
            try:
                return match.group(1)
            except IndexError:
                return match.group(0)

    return None


# ************************************************************ #
# ****************** END OF EBOOK META UTILS ****************** #
# ************************************************************ #


def copy_and_convert_ebook_file(
    pbar: tqdm,
    folder_index: int,
    classification: str | None,
    series_folder_name: str,
    source_ebook_file_path: str,
    target_epub_path: str,
    dont_split_on_page_breaks: bool,
) -> None:
    """
    Copy an eBook file from JLN directory to a Kavita directory.
    """
    # Use calibre-meta to set the series and index
    path = Path(target_epub_path)
    dirpath = Path(tempfile.mkdtemp())
    pbar.update(0.05)
    ebook_filename = os.path.basename(source_ebook_file_path)
    vol_num = extract_volume_number(ebook_filename)
    series_year_num = extract_series_year_number(ebook_filename)
    series_part_num = extract_series_part_number(ebook_filename)
    volume_part_num = extract_volume_part_number(ebook_filename)
    series_name = series_folder_name

    if classification:
        series_name = (
            series_folder_name + f" {convert_classification_to_plural(classification)}"
        )

    pbar.set_postfix(refresh=True, calibre="repairs")
    temp_fixed_epub_file_path = dirpath.joinpath(path.stem + ".temp_fixed.epub")
    convert_thread = Thread(
        target=convert_and_fix_ebook,
        args=(
            source_ebook_file_path,
            os.fspath(temp_fixed_epub_file_path),
            dont_split_on_page_breaks,
        ),
    )
    convert_thread.start()
    while convert_thread.is_alive():
        sleep(1)
        if convert_thread.is_alive():
            pbar.update(0)
    convert_thread.join()
    pbar.update(0.7)

    pbar.set_postfix(refresh=True, calibre="addmeta")
    # must end in a supported eBook file extension to be recognized by calibre's ebook-meta tool
    temp_epub_file_path = dirpath.joinpath(path.stem + ".temp.epub")
    temp_epub_file = shutil.copyfile(
        temp_fixed_epub_file_path, os.fspath(temp_epub_file_path)
    )
    metadata_thread = Thread(
        target=set_epub_series_and_index,
        args=(
            temp_epub_file,
            series_name,
            series_year_num,
            series_part_num,
            vol_num,
            volume_part_num,
            folder_index,
        ),
    )
    metadata_thread.start()
    while metadata_thread.is_alive():
        sleep(1)
        if metadata_thread.is_alive():
            pbar.update(0)
    metadata_thread.join()
    pbar.update(0.2)

    shutil.copyfile(temp_epub_file_path, target_epub_path)
    pbar.update(0.05)
    while is_locked(temp_epub_file) or is_locked(os.fspath(temp_fixed_epub_file_path)):
        pbar.set_postfix(refresh=True, current="waiting")
        time.sleep(0.5)
    pbar.set_postfix(refresh=True, calibre="done...")
    shutil.rmtree(dirpath)


def is_side_story_folder(ebook_file_path_relative: str) -> bool:
    """
    Check if the given path is a side story folder.
    """
    folder_names = [
        "side story",
        "side stories",
        "spin-off series",
    ]
    return any(
        folder_name in ebook_file_path_relative.lower() for folder_name in folder_names
    )


def is_spinoff_series_folder(ebook_file_path_relative: str) -> bool:
    """
    Check if the given path is a spinoff folder.
    """
    folder_names = [
        "spin-off",
        "spinoff",
        "spin off",
    ]
    return any(
        folder_name in ebook_file_path_relative.lower() for folder_name in folder_names
    )


def is_short_story_folder(ebook_file_path_relative: str) -> bool:
    """
    Check if the given path is a short story folder.
    """
    folder_names = [
        "short story",
        "short stories",
    ]
    return any(
        folder_name in ebook_file_path_relative.lower() for folder_name in folder_names
    )


def list_ebook_files(series_folder_path: str) -> list[tuple[str, str | None]]:
    """
    List all eBook files in the given folder, with a classification based on the folder name.
    """
    ebook_extensions: set[str] = {
        ".epub",
        ".azw4",
        ".azw3",
        ".azw",
        ".chm",
        ".djvu",
        ".docx",
        ".fb2",
        ".htlz",
        ".html",
        ".lit",
        ".lrf",
        ".mobi",
        ".odt",
        ".pdb",
        ".pml",
        ".rb",
        ".rtf",
        ".snb",
        ".tcr",
    }
    return [
        (
            os.path.join(dirpath, f),
            classify_ebook_file_type(os.path.relpath(dirpath, series_folder_path)),
        )
        for dirpath, dirnames, filenames in os.walk(series_folder_path)
        for f in filenames
        if (
            os.path.isfile(os.path.join(dirpath, f))
            and any(f.lower().endswith(ext) for ext in ebook_extensions)
        )
    ]


def classify_ebook_file_type(ebook_folder_path_relative: str) -> str | None:
    """
    Classify the type of eBook file based on its filename and subfolders.
    """
    is_side_story = is_side_story_folder(ebook_folder_path_relative)
    is_spinoff_series = is_spinoff_series_folder(ebook_folder_path_relative)
    is_short_story = is_short_story_folder(ebook_folder_path_relative)
    is_fan = "fan" in ebook_folder_path_relative.lower()
    is_official = "official" in ebook_folder_path_relative.lower()
    is_webnovel = "web novel" in ebook_folder_path_relative.lower()
    is_lightnovel = "light novel" in ebook_folder_path_relative.lower()

    translation_type = None
    if is_fan:
        translation_type = "Fan Translation"
    elif is_official:
        translation_type = "Official Translation"

    special_type = None
    if is_side_story:
        special_type = "Side Story"
    elif is_short_story:
        special_type = "Short Story"
    elif is_spinoff_series:
        special_type = "Spin-off"

    book_type = None
    if is_webnovel:
        book_type = "Web Novel"
    elif is_lightnovel:
        book_type = "Light Novel"

    if translation_type and special_type and book_type:
        return f"{book_type} {special_type} {translation_type}"
    elif translation_type and special_type:
        return f"{special_type} {translation_type}"
    elif book_type and special_type:
        return f"{book_type} {special_type}"
    elif translation_type and book_type:
        return f"{book_type} {translation_type}"
    elif translation_type:
        return translation_type
    elif special_type:
        return special_type
    elif book_type:
        return book_type


def convert_classification_to_plural(classification: str) -> str:
    """
    Convert a classification to a plural form.
    """
    if classification.endswith(" Story"):
        return classification.replace(" Story", " Stories")
    else:
        return classification


def copy_and_convert_ebook_files(
    src_dir: str, target_dir: str, dont_split_on_page_breaks: bool
) -> None:
    """
    Copy and convert eBook files recursively from source directory to the target Kavita directory.
    """
    src = os.path.abspath(src_dir)
    target = os.path.abspath(target_dir)

    if not os.path.isdir(src):
        raise argparse.ArgumentTypeError(f"Source directory does not exist: {src_dir}")

    if not os.path.exists(target):
        os.makedirs(target)

    for series_folder in os.listdir(src):
        series_folder_path = os.path.join(src, series_folder)

        if not os.path.isdir(series_folder_path):
            continue

        target_series_folder = os.path.join(target, series_folder)
        if not os.path.exists(target_series_folder):
            os.makedirs(target_series_folder)

        ebook_file_paths = list_ebook_files(series_folder_path)
        if not ebook_file_paths:
            continue

        print(f"{series_folder}:")
        with tqdm(
            ebook_file_paths,
            dynamic_ncols=True,
            total=len(ebook_file_paths),
            miniters=0,
            bar_format="{desc}: "
            + "{percentage:.3f}%|{bar}| "
            + "{n:.2f}/{total_fmt} "
            + "[{elapsed}<{remaining}, {rate_fmt}{postfix}]",
        ) as pbar:
            for index, (ebook_file_path, classification) in enumerate(ebook_file_paths):
                path = Path(ebook_file_path)
                filename = path.stem
                if classification:
                    filename += f" - {classification}"
                filename += path.suffix
                target_epub_path = os.path.join(target_series_folder, filename)
                if os.path.exists(target_epub_path) and os.path.exists(ebook_file_path):
                    # compare modified times
                    target_mtime = os.path.getmtime(target_epub_path)
                    src_mtime = os.path.getmtime(ebook_file_path)
                    if target_mtime > src_mtime:
                        pbar.update(1)
                        continue

                copy_and_convert_ebook_file(
                    pbar,
                    index,
                    classification,
                    series_folder,
                    ebook_file_path,
                    target_epub_path,
                    dont_split_on_page_breaks,
                )

                if index == len(ebook_file_paths) - 1:
                    pbar.set_postfix(refresh=True)


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Copy eBook files from one directory to another",
        exit_on_error=False,
    )
    parser.add_argument("-s", "--src", help="source directory")
    parser.add_argument("-t", "--target", help="target directory")
    parser.add_argument(
        "--dont-split-on-page-breaks",
        default=False,
        required=False,
        action=argparse.BooleanOptionalAction,
        help="Turn off splitting at page breaks. "
        + "Normally, input files are automatically split at every page break "
        + "into two files. This gives an output e-book that can be parsed "
        + "faster and with less resources. However, splitting is slow and "
        + "if your source file contains a very large number of page breaks, "
        + "you should turn off splitting on page breaks.",
    )
    args = parser.parse_args()

    if os.path.abspath(args.src) == os.path.abspath(args.target):
        print("Source and target directories must not be the same.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.src):
        print(f"Source directory does not exist: {args.src}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(args.src):
        print(f"Source is not a directory: {args.src}", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(args.target):
        if not os.path.isdir(args.target):
            print(f"Target is not a directory: {args.target}", file=sys.stderr)
            sys.exit(1)
    else:
        os.makedirs(args.target)

    try:
        copy_and_convert_ebook_files(
            args.src, args.target, args.dont_split_on_page_breaks
        )
    except argparse.ArgumentTypeError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
