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
                              volume_part_num: str | None) -> None:
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
            index += f'.{volume_part_num}'
        command += ['--index', index]
    else:
        # Default volume number is 1 when applying the series title and the index is not specified,
        # so we still want to apply the part number to the series index
        if volume_part_num:
            index = f'1.{volume_part_num}'
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


def copy_epub_file(index: int, series_folder_path: str, series_folder_name: str, epub_file_path: str, dest_epub_path: str) -> None:
    '''
    Copy an epub file from JLN directory to a Kavita directory.
    '''
    # Use calibre-meta to set the series and index
    temp_epub_file = shutil.copy(epub_file_path, dest_epub_path + ".temp.epub")
    epub_filename = os.path.basename(epub_file_path)
    vol_num = extract_volume_number(epub_filename)
    series_part_num = extract_series_part_number(epub_filename)
    volume_part_num = extract_volume_part_number(epub_filename)
    series_name = series_folder_name

    epub_file_path_relative = os.path.relpath(epub_file_path, series_folder_path)
    is_side_story = is_side_story_folder(epub_file_path_relative)
    if is_side_story:
        series_name = series_folder_name + " - Side Stories"

    is_short_story = is_short_story_folder(epub_file_path_relative)
    if is_short_story:
        series_name = series_folder_name + " - Short Stories"
    
    if vol_num is None:
        vol_num = f'{index}'
    

    set_epub_series_and_index(
        temp_epub_file,
        series_name,
        series_part_num,
        vol_num,
        volume_part_num
    )

    shutil.copyfile(temp_epub_file, dest_epub_path)
    while is_locked(temp_epub_file):
        time.sleep(2)
    os.remove(temp_epub_file)

def is_side_story_folder(epub_file_path_relative: str) -> bool:
    folder_names = [
        "side story",
        "side stories",
    ]
    return any(folder_name in epub_file_path_relative.lower() for folder_name in folder_names)

def is_short_story_folder(epub_file_path_relative: str) -> bool:
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


def find_series_epub_files(series_folder_path: str) -> list[str]:
    '''
    Find the epub files in the given series folder, with a preference for the official translations.

    Possible paths:

    - `/Series/Part */EPUB/*.epub`
    - `/Series/EPUB/*.epub`
    - `/Series/EPUB/Official/*.epub`
    - `/Series/Official/EPUB/*.epub`
    - `/Series/Official/*.epub`
    - `/Series/*.epub`
    - `/Series/Light Novel/EPUB/*.epub`
    - `/Series/Side Story/EPUB/*.epub`
    - `/Series/EPUB/Side Story/*.epub`
    - `/Series/Part */EPUB/Side Story/*.epub`
    - `/Series/Side Stories/EPUB/*.epub`
    - `/Series/EPUB/Side Stories/*.epub`
    - `/Series/Part */EPUB/Side Stories/*.epub`
    '''
    root_lightnovel_folder = find_lightnovel_folder(series_folder_path)

    root_official_folder = find_official_folder(root_lightnovel_folder)
    root_sidestory_folder = find_sidestory_folder(root_lightnovel_folder)
    root_part_folders = find_part_folders(root_lightnovel_folder)
    epub_folder_path = os.path.join(root_lightnovel_folder, 'EPUB')
    has_root_epub_folder = os.path.isdir(epub_folder_path)
    if root_official_folder:
        official_epub_folder_path = os.path.join(
            root_official_folder, 'EPUB')
        has_epub_folder = os.path.isdir(official_epub_folder_path)
        if has_epub_folder:
            epub_folder_path = official_epub_folder_path
        else:
            epub_folder_path = root_official_folder
    elif has_root_epub_folder:
        # find official subfolder from folder
        official_folder = find_official_folder(epub_folder_path)
        if official_folder:
            epub_folder_path = official_folder
    else:
        epub_folder_path = root_lightnovel_folder
    sub_sidestory_folder = find_sidestory_folder(epub_folder_path)

    epub_files = []
    if root_sidestory_folder:
        epub_files += list_epub_files(root_sidestory_folder)

    if root_part_folders:
        for part_folder in root_part_folders:
            part_epub_folder_path = os.path.join(part_folder, 'EPUB')
            has_part_epub_folder = os.path.isdir(part_epub_folder_path)
            if has_part_epub_folder:
                # find official subfolder from folder
                official_folder = find_official_folder(part_epub_folder_path)
                sidestory_folder = find_sidestory_folder(part_epub_folder_path)
                if official_folder:
                    part_epub_folder_path = official_folder
                epub_files += list_epub_files(part_epub_folder_path)
                if sidestory_folder:
                    epub_files += list_epub_files(sidestory_folder)
            else:
                sidestory_folder = find_sidestory_folder(part_folder)
                epub_files += list_epub_files(part_folder)
                if sidestory_folder:
                    epub_files += list_epub_files(sidestory_folder)
        return epub_files
    
    epub_files += list_epub_files(epub_folder_path)
    if sub_sidestory_folder:
        epub_files += list_epub_files(sub_sidestory_folder)

    return epub_files

def list_epub_files(epub_folder_path) -> list[str]:
    return [os.path.join(epub_folder_path, f)
            for f in os.listdir(epub_folder_path)
            if os.path.isfile(os.path.join(epub_folder_path, f))
            and f.lower().endswith('.epub')]

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
        for index, epub_file_path in enumerate(pbar):
            dest_epub_path = os.path.join(
                dest_series_folder, os.path.basename(epub_file_path))
            if os.path.exists(dest_epub_path):
                pbar.update(1)
                continue

            copy_epub_file(index, series_folder_path, series_folder, epub_file_path, dest_epub_path)


def find_lightnovel_folder(series_folder_path: str) -> str:
    '''Find the light novel folder in the given folder, or `series_folder_path` if it is not found
    '''
    for series_sub_folder in os.listdir(series_folder_path):
        series_sub_folder_path = os.path.join(
            series_folder_path, series_sub_folder)
        if os.path.isdir(series_sub_folder_path) and 'light novel' in series_sub_folder.lower():
            return series_sub_folder_path
    return series_folder_path


def find_official_folder(epub_folder_path) -> str | None:
    '''Find the official folder in the given folder, or None if it does not exist
    '''
    for epub_sub_folder in os.listdir(epub_folder_path):
        epub_sub_folder_path = os.path.join(
            epub_folder_path, epub_sub_folder)
        if os.path.isdir(epub_sub_folder_path) and 'official' in epub_sub_folder.lower():
            return epub_sub_folder_path
    return None


def find_sidestory_folder(epub_folder_path) -> str | None:
    '''Find the side story folder in the given folder, or None if it does not exist
    '''
    for epub_sub_folder in os.listdir(epub_folder_path):
        epub_sub_folder_path = os.path.join(
            epub_folder_path, epub_sub_folder)
        if os.path.isdir(epub_sub_folder_path) and (is_side_story_folder(epub_sub_folder) or is_short_story_folder(epub_sub_folder)):
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
