'''
Script to convert a JLN epub directory structure to a Kavita directory structure.
'''

import os
import sys
import shutil
import argparse
import re
import subprocess
from tqdm import tqdm


def set_epub_series_and_index(epub_file_path, series_title, series_index):
    '''
    Set the series and index of an epub file using calibre.
    '''
    # Construct the command
    command = ['ebook-meta', epub_file_path, '--series', series_title]

    if series_index is not None:
        command += ['--index', str(series_index)]

    # Run the command
    result = subprocess.run(command, capture_output=True, check=False)

    # Check the output for errors
    if result.returncode != 0:
        print('Error:', result.stderr.decode('utf-8'))


VOLUME_PATTERNS = [
    re.compile(r't[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
    re.compile(r'v[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
    re.compile(r'vol[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
    re.compile(r'volume[\s.-]*(\d+(\.\d+)?)', re.IGNORECASE),
    re.compile(r'LN[\s]*(\d+(\.\d+)?)', re.IGNORECASE),
    re.compile(r'\b\d+(?:\.\d+)?\b'),
]


def extract_volume_number(string):
    '''
    Extract the volume number from the filename.
    '''
    for pattern in VOLUME_PATTERNS:
        match = pattern.search(string)
        if match:
            try:
                return match.group(1)
            except IndexError:
                return match.group(0)
    return None


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

        epub_folder_path = os.path.join(series_folder_path, 'EPUB')

        # Possible paths:
        #   TODO: /Series/Part */EPUB/*.epub
        #   /Series/EPUB/*.epub
        #   /Series/EPUB/Official/*.epub
        #   /Series/Official/EPUB/*.epub
        #   /Series/*.epub

        if not os.path.isdir(epub_folder_path):
            # Skips Ascendence of a Bookworm
            continue

        official_folder_found = False
        for epub_sub_folder in os.listdir(epub_folder_path):
            epub_sub_folder_path = os.path.join(
                epub_folder_path, epub_sub_folder)
            if os.path.isdir(epub_sub_folder_path) and 'official' in epub_sub_folder.lower():
                epub_folder_path = epub_sub_folder_path
                official_folder_found = True
                break

        if not official_folder_found:
            for series_sub_folder in os.listdir(series_folder_path):
                series_sub_folder_path = os.path.join(
                    series_folder_path, series_sub_folder)
                if os.path.isdir(series_sub_folder_path) \
                        and 'official' in series_sub_folder.lower():

                    epub_temp_path = os.path.join(
                        series_sub_folder_path, 'EPUB')
                    if os.path.exists(epub_temp_path):
                        epub_folder_path = epub_temp_path
                    else:
                        epub_folder_path = series_sub_folder_path
                    official_folder_found = True
                    break

        dest_series_folder = os.path.join(dest, series_folder)
        if not os.path.exists(dest_series_folder):
            os.makedirs(dest_series_folder)

        epub_files = [os.path.join(epub_folder_path, f)
                      for f in os.listdir(epub_folder_path)
                      if os.path.isfile(os.path.join(epub_folder_path, f))
                      and f.lower().endswith('.epub')]

        if not epub_files:
            continue

        print(f'{series_folder}:')
        pbar = tqdm(epub_files)
        for epub_file in pbar:
            dest_epub = os.path.join(
                dest_series_folder, os.path.basename(epub_file))
            if os.path.exists(dest_epub):
                pbar.update(1)
                continue

            # Use calibre-meta to set the series and index
            temp_epub_file = dest_epub + ".temp.epub"
            shutil.copy(epub_file, temp_epub_file)
            vol_num = extract_volume_number(os.path.basename(epub_file))
            set_epub_series_and_index(temp_epub_file, series_folder, vol_num)
            shutil.move(temp_epub_file, dest_epub)


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
