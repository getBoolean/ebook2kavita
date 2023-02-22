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


def is_locked(filepath):
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


def set_epub_series_and_index(epub_file_path: str, series_title: str,
                              series_part_num: str | None, volume_num: str | None,
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

            try:
                return match.group(1)
            except IndexError:
                return match.group(0)

    return None


def extract_volume_part_number(filename: str) -> str | None:
    '''
    Extract the part number from the filename.
    '''

    for pattern in PART_PATTERNS:
        match = pattern.search(filename)
        if match:
            # Check that series part pattern must come after VOLUME_PATTERNS
            for volume_pattern in VOLUME_PATTERNS:
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

    if not extract_series_part_number(filename):
        match = BACKUP_VOLUME_PATTERN.search(filename)
        if match:
            try:
                return match.group(1)
            except IndexError:
                return match.group(0)

    return None


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
    '''
    root_official_folder = find_official_folder(series_folder_path)
    root_part_folders = find_part_folders(series_folder_path)
    epub_folder_path = os.path.join(series_folder_path, 'EPUB')
    has_root_epub_folder = os.path.isdir(epub_folder_path)
    if has_root_epub_folder:
        # find official subfolder from folder
        official_folder = find_official_folder(epub_folder_path)
        if official_folder:
            epub_folder_path = official_folder
    elif root_official_folder:
        official_epub_folder_path = os.path.join(
            root_official_folder, 'EPUB')
        has_epub_folder = os.path.isdir(official_epub_folder_path)
        if has_epub_folder:
            epub_folder_path = official_epub_folder_path
        else:
            epub_folder_path = root_official_folder
    else:
        epub_folder_path = series_folder_path

    if root_part_folders:
        epub_files = []
        for part_folder in root_part_folders:
            part_epub_folder_path = os.path.join(part_folder, 'EPUB')
            has_part_epub_folder = os.path.isdir(part_epub_folder_path)
            if has_part_epub_folder:
                # find official subfolder from folder
                official_folder = find_official_folder(part_epub_folder_path)
                if official_folder:
                    part_epub_folder_path = official_folder
                epub_files += [os.path.join(part_epub_folder_path, f)
                               for f in os.listdir(part_epub_folder_path)
                               if os.path.isfile(os.path.join(part_epub_folder_path, f))
                               and f.lower().endswith('.epub')]
            else:
                epub_files += [os.path.join(part_folder, f)
                               for f in os.listdir(part_folder)
                               if os.path.isfile(os.path.join(part_folder, f))
                               and f.lower().endswith('.epub')]
        return epub_files

    return [os.path.join(epub_folder_path, f)
            for f in os.listdir(epub_folder_path)
            if os.path.isfile(os.path.join(epub_folder_path, f))
            and f.lower().endswith('.epub')]


def copy_epub_file(series_folder_name, epub_file_path, dest_epub_path):
    '''
    Copy an epub file from JLN directory to a Kavita directory.
    '''
    # Use calibre-meta to set the series and index
    temp_epub_file = shutil.copy(epub_file_path, dest_epub_path + ".temp.epub")
    epub_filename = os.path.basename(epub_file_path)
    vol_num = extract_volume_number(epub_filename)
    series_part_num = extract_series_part_number(epub_filename)
    volume_part_num = extract_volume_part_number(epub_filename)
    set_epub_series_and_index(
        temp_epub_file, series_folder_name,
        series_part_num, vol_num, volume_part_num)
    shutil.copyfile(temp_epub_file, dest_epub_path)
    while is_locked(temp_epub_file):
        time.sleep(2)
    os.remove(temp_epub_file)


def copy_epub_files(src_dir, dest_dir):
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
        for epub_file_path in pbar:
            dest_epub_path = os.path.join(
                dest_series_folder, os.path.basename(epub_file_path))
            if os.path.exists(dest_epub_path):
                pbar.update(1)
                continue

            copy_epub_file(series_folder, epub_file_path, dest_epub_path)


def find_official_folder(epub_folder_path) -> str | None:
    '''Find the official folder in the given folder, or None if it does not exist
    '''
    for epub_sub_folder in os.listdir(epub_folder_path):
        epub_sub_folder_path = os.path.join(
            epub_folder_path, epub_sub_folder)
        if os.path.isdir(epub_sub_folder_path) and 'official' in epub_sub_folder.lower():
            return epub_sub_folder_path
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Copy EPUB files from one directory to another')
    parser.add_argument('src_dir', help='source directory')
    parser.add_argument('dest_dir', help='destination directory')
    args = parser.parse_args()

    try:
        copy_epub_files(args.src_dir, args.dest_dir)
    except argparse.ArgumentTypeError as e:
        print(str(e))
        sys.exit(1)
