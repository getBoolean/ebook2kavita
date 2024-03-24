'''
Script to convert a JLN epub directory structure to a Kavita directory structure.
'''

import os
import time
import sys
import shutil
import argparse
import re
import subprocess
from pathlib import Path

from tqdm import tqdm


# ************************************************************ #
# ***************** START OF EPUB META UTILS ***************** #
# ************************************************************ #


VOLUME_PATTERNS: list = [
    re.compile(r'v[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
    re.compile(r'vol[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
    re.compile(r'volume[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
    re.compile(r'LN[\s]*(\d+(\.\d+)?)', re.IGNORECASE),
]

BACKUP_VOLUME_PATTERN = re.compile(r'\b\d+(?:\.\d+)?\b')

PART_PATTERNS: list = [
    re.compile(r'part[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
    re.compile(r'pt[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
]

SIDESTORY_PATTERNS: list = [
    re.compile(r'ss[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
    re.compile(r'extra[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
    re.compile(r'special[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
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
            file_object = open(filepath, 'a', buffer_size, encoding='utf-8')
            if file_object:
                locked = False
        except IOError:
            locked = True
        finally:
            if file_object:
                file_object.close()
    return locked


def set_epub_series_and_index(epub_file_path: str,
                              series_title: str,
                              series_part_num: str | None,
                              volume_num: str | None,
                              volume_part_num: str | None,
                              folder_index: int) -> None:
    '''
    Set the series and index of an epub file using calibre.
    '''
    # Construct the command
    title: str = series_title
    if series_part_num:
        title = f'{series_title} Part {series_part_num}'

    command = ['ebook-meta', epub_file_path, '--series', title]

    if volume_num is not None:
        index = volume_num
        if volume_part_num:
            index += f'{volume_num}.{volume_part_num}'
        command += ['--index', index]
    else:
        index = f'1.{folder_index}'
        command += ['--index', index]

    while is_locked(epub_file_path):
        time.sleep(2)
    # Run the command
    result = subprocess.run(command, capture_output=True, check=False)

    # Check the output for errors
    if result.returncode != 0:
        print('Error:', result.stderr.decode('utf-8'))


def extract_series_part_number(filename: str) -> str | None:
    '''
    Extract the part number from the filename.
    '''

    for pattern in PART_PATTERNS:
        match = pattern.search(filename)
        if match:
            # Check that series part pattern must come before VOLUME_PATTERNS
            for volume_pattern in VOLUME_PATTERNS:
                volume_match = volume_pattern.search(filename)
                if volume_match and volume_match.start() < match.start():
                    return None

            for volume_pattern in SIDESTORY_PATTERNS:
                volume_match = volume_pattern.search(filename)
                if volume_match and volume_match.start() < match.start():
                    return None

            try:
                return match.group(1)
            except IndexError:
                return match.group(0)

    return None


def extract_volume_part_number(filename: str) -> str | None:
    '''
    Extract the part number from the filename.

    Note that this won't work for files with both series parts and volume parts
    such as `Title Part 2 - Volume 1 Part 2`. It will (likely) return None.
    '''

    for pattern in PART_PATTERNS:
        match = pattern.search(filename)
        if match:
            # Check that series part pattern must come after VOLUME_PATTERNS
            for volume_pattern in VOLUME_PATTERNS:
                volume_match = volume_pattern.search(filename)
                if volume_match and volume_match.start() > match.start():
                    return None

            for volume_pattern in SIDESTORY_PATTERNS:
                volume_match = volume_pattern.search(filename)
                if volume_match and volume_match.start() > match.start():
                    return None

            try:
                return match.group(1)
            except IndexError:
                return match.group(0)

    return None


def extract_volume_number(filename: str) -> str | None:
    '''
    Extract the volume number from the filename.
    '''

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
# ****************** END OF EPUB META UTILS ****************** #
# ************************************************************ #


def copy_epub_file(folder_index: int,
                   classification: str | None,
                   series_folder_name: str,
                   epub_file_path: str,
                   dest_epub_path: str) -> None:
    '''
    Copy an epub file from JLN directory to a Kavita directory.
    '''
    # Use calibre-meta to set the series and index
    path = Path(dest_epub_path)
    temp_epub_file_path = path.parent.joinpath(path.stem + '.temp.epub')
    temp_epub_file = shutil.copy(epub_file_path, os.fspath(temp_epub_file_path))
    epub_filename = os.path.basename(epub_file_path)
    vol_num = extract_volume_number(epub_filename)
    series_part_num = extract_series_part_number(epub_filename)
    volume_part_num = extract_volume_part_number(epub_filename)
    series_name = series_folder_name

    if classification:
        series_name = series_folder_name + f' - {convert_classification_to_plural(classification)}'

    set_epub_series_and_index(
        temp_epub_file,
        series_name,
        series_part_num,
        vol_num,
        volume_part_num,
        folder_index
    )

    shutil.copyfile(temp_epub_file, dest_epub_path)
    while is_locked(temp_epub_file):
        time.sleep(2)
    os.remove(temp_epub_file)

def is_side_story_folder(epub_file_path_relative: str) -> bool:
    '''
    Check if the given path is a side story folder.
    '''
    folder_names = [
        "side story",
        "side stories",
    ]
    return any(folder_name in epub_file_path_relative.lower() for folder_name in folder_names)

def is_short_story_folder(epub_file_path_relative: str) -> bool:
    '''
    Check if the given path is a short story folder.
    '''
    folder_names = [
        "short story",
        "short stories",
    ]
    return any(folder_name in epub_file_path_relative.lower() for folder_name in folder_names)


def find_part_folders(series_folder_path: str) -> list[str]:
    '''Find the part folders in the given folder
    '''
    part_folders = []
    for series_sub_folder in os.listdir(series_folder_path):
        series_sub_folder_path = os.path.join(
            series_folder_path, series_sub_folder)
        if os.path.isdir(series_sub_folder_path) and 'part' in series_sub_folder.lower():
            part_folders.append(series_sub_folder_path)
    return part_folders


def find_series_epub_files(series_folder_path: str) -> list[tuple[str, str | None]]:
    '''
    Find the epub files in the given series folder, with a preference for the official translations.

    Possible paths:

    - `Part */EPUB/*.epub`
    - `Part */EPUB/Side Story/*.epub`
    - `Part */EPUB/Side Stories/*.epub`
    - `EPUB/*.epub`
    - `EPUB/Official/*.epub`
    - `Official*/EPUB/*.epub`
    - `Official*/*.epub`
    - `Fan*/EPUB/*.epub`
    - `Fan*/*.epub`
    - `*.epub`
    - `Light Novel/EPUB/*.epub`
    - `Side Story/EPUB/*.epub`
    - `EPUB/Side Story/*.epub`
    - `Side Stories/EPUB/*.epub`
    - `EPUB/Side Stories/*.epub`
    '''
    root_lightnovel_folder = find_lightnovel_folder(series_folder_path)

    root_official_folder = find_official_folder(root_lightnovel_folder)
    root_fan_folder = find_fan_folder(root_lightnovel_folder)
    root_part_folders = find_part_folders(root_lightnovel_folder)
    root_epub_folder_path = os.path.join(root_lightnovel_folder, 'EPUB')
    has_root_epub_folder = os.path.isdir(root_epub_folder_path)
    epub_files: list[tuple[str, str | None]] = []
    epub_files += list_epub_files(root_lightnovel_folder, series_folder_path)
    if root_official_folder:
        epub_files += list_epub_files(root_official_folder, series_folder_path)
        official_epub_folder_path = os.path.join(
            root_official_folder, 'EPUB')
        has_epub_folder = os.path.isdir(official_epub_folder_path)
        if has_epub_folder:
            epub_files += list_epub_files(official_epub_folder_path, series_folder_path)

        digial_edition_folder = find_digital_edition_folder(root_official_folder)
        if digial_edition_folder:
            epub_files += list_epub_files(digial_edition_folder, series_folder_path)
            official_epub_folder_path = os.path.join(
                digial_edition_folder, 'EPUB')
            has_epub_folder = os.path.isdir(official_epub_folder_path)
            if has_epub_folder:
                epub_files += list_epub_files(official_epub_folder_path, series_folder_path)


    if root_fan_folder:
        epub_files += list_epub_files(root_fan_folder, series_folder_path)
        fan_epub_folder_path = os.path.join(
            root_fan_folder, 'EPUB')
        has_epub_folder = os.path.isdir(fan_epub_folder_path)
        if has_epub_folder:
            epub_files += list_epub_files(fan_epub_folder_path, series_folder_path)

    if has_root_epub_folder:
        epub_files += list_epub_files(root_epub_folder_path, series_folder_path)
        sub_official_folder = find_official_folder(root_epub_folder_path)
        if sub_official_folder:
            epub_files += list_epub_files(sub_official_folder, series_folder_path)
            sub_sidestory_folder = find_sidestory_folder(sub_official_folder)
            if sub_sidestory_folder:
                epub_files += list_epub_files(sub_sidestory_folder, series_folder_path)

        sub_fan_folder = find_fan_folder(root_epub_folder_path)
        if sub_fan_folder:
            epub_files += list_epub_files(sub_fan_folder, series_folder_path)
            sub_sidestory_folder = find_sidestory_folder(sub_fan_folder)
            if sub_sidestory_folder:
                epub_files += list_epub_files(sub_sidestory_folder, series_folder_path)

        sub_sidestory_folder = find_sidestory_folder(root_epub_folder_path)
        if sub_sidestory_folder:
            epub_files += list_epub_files(sub_sidestory_folder, series_folder_path)

    root_sidestory_folder = find_sidestory_folder(root_lightnovel_folder)
    if root_sidestory_folder:
        epub_files += list_epub_files(root_sidestory_folder, series_folder_path)

    if root_part_folders:
        for part_folder in root_part_folders:
            sub_epub_folder_path = os.path.join(part_folder, 'EPUB')
            has_sub_epub_folder = os.path.isdir(sub_epub_folder_path)
            if has_sub_epub_folder:
                # find official subfolder from folder
                sub_official_folder = find_official_folder(sub_epub_folder_path)
                sub_fan_folder = find_fan_folder(sub_epub_folder_path)
                epub_files += list_epub_files(sub_epub_folder_path, series_folder_path)
                if sub_official_folder:
                    epub_files += list_epub_files(sub_official_folder, series_folder_path)
                    sub_sidestory_folder = find_sidestory_folder(sub_official_folder)
                    if sub_sidestory_folder:
                        epub_files += list_epub_files(sub_sidestory_folder, series_folder_path)
                if sub_fan_folder:
                    epub_files += list_epub_files(sub_fan_folder, series_folder_path)
                    sub_sidestory_folder = find_sidestory_folder(sub_fan_folder)
                    if sub_sidestory_folder:
                        epub_files += list_epub_files(sub_sidestory_folder, series_folder_path)
                sidestory_folder = find_sidestory_folder(sub_epub_folder_path)
                if sidestory_folder:
                    epub_files += list_epub_files(sidestory_folder, series_folder_path)
            else:
                sub_official_folder = find_official_folder(part_folder)
                sub_fan_folder = find_fan_folder(part_folder)
                epub_files += list_epub_files(part_folder, series_folder_path)
                if sub_official_folder:
                    epub_files += list_epub_files(sub_official_folder, series_folder_path)
                    sub_sidestory_folder = find_sidestory_folder(sub_official_folder)
                    if sub_sidestory_folder:
                        epub_files += list_epub_files(sub_sidestory_folder, series_folder_path)
                if sub_fan_folder:
                    epub_files += list_epub_files(sub_fan_folder, series_folder_path)
                    sub_sidestory_folder = find_sidestory_folder(sub_fan_folder)
                    if sub_sidestory_folder:
                        epub_files += list_epub_files(sub_sidestory_folder, series_folder_path)
                sidestory_folder = find_sidestory_folder(part_folder)
                if sidestory_folder:
                    epub_files += list_epub_files(sidestory_folder, series_folder_path)

    return epub_files

def list_epub_files(epub_folder_path: str, series_folder_path: str) -> list[tuple[str, str | None]]:
    '''
    List all epub files in the given folder, with a classification based on the folder name.
    '''
    epub_folder_path_relative = os.path.relpath(epub_folder_path, series_folder_path)
    classification = classify_epub_file_type(epub_folder_path_relative)
    return [(os.path.join(epub_folder_path, f), classification)
            for f in os.listdir(epub_folder_path)
            if os.path.isfile(os.path.join(epub_folder_path, f))
            and f.lower().endswith('.epub')]

def classify_epub_file_type(epub_folder_path_relative: str) -> str | None:
    '''
    Classify the type of epub file based on its filename.
    '''
    if is_side_story_folder(epub_folder_path_relative):
        return "Side Story"
    elif is_short_story_folder(epub_folder_path_relative):
        return "Short Story"
    elif "fan" in epub_folder_path_relative.lower():
        return "Fan Translation"
    elif "official" in epub_folder_path_relative.lower():
        return "Official Translation"
    else:
        return None

def convert_classification_to_plural(classification: str) -> str:
    '''
    Convert a classification to a plural form.
    '''
    if classification == "Side Story":
        return "Side Stories"
    elif classification == "Short Story":
        return "Short Stories"
    elif classification == "Fan Translation":
        return "Fan Translations"
    elif classification == "Official Translation":
        return "Official Translations"
    else:
        return classification

def copy_epub_files(src_dir: str, dest_dir: str) -> None:
    '''
    Copy epub files from JLN directory to a Kavita directory.
    '''
    src = os.path.abspath(src_dir)
    dest = os.path.abspath(dest_dir)

    if not os.path.isdir(src):
        raise argparse.ArgumentTypeError(
            f'Source directory does not exist: {src_dir}')

    if not os.path.exists(dest):
        os.makedirs(dest)

    for series_folder in os.listdir(src):
        series_folder_path = os.path.join(src, series_folder)

        if not os.path.isdir(series_folder_path):
            continue

        dest_series_folder = os.path.join(dest, series_folder)
        if not os.path.exists(dest_series_folder):
            os.makedirs(dest_series_folder)

        epub_file_paths = find_series_epub_files(series_folder_path)
        if not epub_file_paths:
            continue

        print(f'{series_folder}:')
        pbar = tqdm(epub_file_paths)
        for index, (epub_file_path, classification) in enumerate(pbar):
            path = Path(epub_file_path)
            filename = path.stem
            if classification:
                filename += f' - {classification}'
            filename += path.suffix
            dest_epub_path = os.path.join(
                dest_series_folder, filename)
            if os.path.exists(dest_epub_path):
                pbar.update(1)
                continue

            copy_epub_file(index, classification, series_folder, epub_file_path, dest_epub_path)


def find_lightnovel_folder(series_folder_path: str) -> str:
    '''Find the light novel folder in the given folder, or `series_folder_path` if it is not found
    '''
    for series_sub_folder in os.listdir(series_folder_path):
        series_sub_folder_path = os.path.join(
            series_folder_path, series_sub_folder)
        path_relative = os.path.relpath(series_sub_folder, series_folder_path)
        if os.path.isdir(series_sub_folder_path) and 'light novel' in path_relative.lower():
            return series_sub_folder_path
    return series_folder_path


def find_official_folder(epub_folder_path: str) -> str | None:
    '''Find the official folder in the given folder, or None if it does not exist
    '''
    for epub_sub_folder in os.listdir(epub_folder_path):
        epub_sub_folder_path = os.path.join(
            epub_folder_path, epub_sub_folder)
        path_relative = os.path.relpath(epub_sub_folder, epub_folder_path)
        if os.path.isdir(epub_sub_folder_path) and 'official' in path_relative.lower():
            return epub_sub_folder_path
    return None


def find_digital_edition_folder(epub_folder_path: str) -> str | None:
    '''Find the digital edition folder in the given folder, or None if it does not exist
    '''
    for epub_sub_folder in os.listdir(epub_folder_path):
        epub_sub_folder_path = os.path.join(
            epub_folder_path, epub_sub_folder)
        path_relative = os.path.relpath(epub_sub_folder, epub_folder_path)
        if os.path.isdir(epub_sub_folder_path) and 'digital edition' in path_relative.lower():
            return epub_sub_folder_path
    return None


def find_fan_folder(epub_folder_path: str) -> str | None:
    '''Find the fan folder in the given folder, or None if it does not exist
    '''
    for epub_sub_folder in os.listdir(epub_folder_path):
        epub_sub_folder_path = os.path.join(
            epub_folder_path, epub_sub_folder)
        path_relative = os.path.relpath(epub_sub_folder, epub_folder_path)
        if os.path.isdir(epub_sub_folder_path) and 'fan' in path_relative.lower():
            return epub_sub_folder_path
    return None


def find_sidestory_folder(epub_folder_path: str) -> str | None:
    '''Find the side story folder in the given folder, or None if it does not exist
    '''
    for epub_sub_folder in os.listdir(epub_folder_path):
        epub_sub_folder_path = os.path.join(
            epub_folder_path, epub_sub_folder)
        path_relative = os.path.relpath(epub_sub_folder, epub_folder_path)
        is_side_story = is_side_story_folder(path_relative) or is_short_story_folder(path_relative)
        if os.path.isdir(epub_sub_folder_path) and is_side_story:
            return epub_sub_folder_path
    return None


def main() -> None:
    '''Main entry point for the script.
    '''
    parser = argparse.ArgumentParser(
        description='Copy EPUB files from one directory to another', exit_on_error=False)
    parser.add_argument('src_dir', help='source directory')
    parser.add_argument('dest_dir', help='destination directory')
    args = parser.parse_args()

    try:
        copy_epub_files(args.src_dir, args.dest_dir)
    except argparse.ArgumentTypeError as error:
        print(str(error))
        sys.exit(1)


if __name__ == '__main__':
    main()
