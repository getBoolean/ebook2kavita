# ebook2kavita

Converts an eBook folder structure to a Kavita folder structure, adding required metadata and repairing malformed EPUB files.

## Features

- Groups ebook files into Kavita series based on subfolders and filenames
- Repair malformed `.epub` files. *(In rare cases this may be very slow even with `--dont-split-on-page-breaks` enabled)*
- Convert eBook non-EPUB files to EPUB (See [Supported file extensions](#supported-file-extensions))
- Automatically run Calibre plugin [DeDRM](https://github.com/noDRM/DeDRM_tools) *(only if installed)*

## Usage

### Requirements

- [Python 3.11+](https://www.python.org/downloads/)
- [Calibre 7+](https://calibre-ebook.com/) *(plus installation directory in `PATH`)*

### Running the script

1. Install software listed in [Requirements](#requirements)
1. Clone this repository and open Powershell to the repository directory
1. Install the python dependencies: `pip install -r requirements.txt`
1. Start the script with the following command:

```bash
python ebook2kavita.py --src "SOURCE_DIR" --target "TARGET_DIR"

# Example: python ebook2kavita.py --src "B:\Dropbox\Personal\Books\Light Novels, Manga\Just Light Novels" --target "B:\Media Server\Light Novels"
```

### Arguments

- `--src`: Source directory, see [Source Folder Structure](#source-folder-structure)
- `--target`: Target directory
- `--dont-split-on-page-breaks`: Turn off splitting at page breaks. Normally, input files are automatically split at every page break into two files. This gives an output e-book that can be parsed faster and with less resources. However, splitting is slow and if your source file contains a very large number of page breaks, you should turn off splitting on page breaks. ([Calibre ebook-convert](https://manual.calibre-ebook.com/generated/en/ebook-convert.html#cmdoption-ebook-convert-epub-output-dont-split-on-page-breaks))
- `--no-svg-cover`: Do not use SVG for the book cover. Use this option if your EPUB is going to be used on a device that does not support SVG, like the iPhone or the JetBook Lite. Without this option, such devices will display the cover as a blank page. ([Calibre ebook-convert](https://manual.calibre-ebook.com/generated/en/ebook-convert.html#cmdoption-ebook-convert-epub-output-no-svg-cover))

## About

- Adds the series name and volume number to the eBook metadata required by Kavita
  - Series name: The first folder in the eBook's path under the source directory, plus the classification (see [Source folder structure](#source-folder-structure)) and series part number
  - Volume number: Extracted from the eBook filename using regex.
  - Volume part number: Extracted from the eBook filename using regex. Must be after the volume number.
  - Series part number: Extracted from the subfolder and filename using regex. Must be before the volume number.
- Splits eBooks from certain classification subfolders into separate series. They can have multiple classifications if the folders are nested
- Supported series classifications (case intensitive):
  - Light Novel
  - Web Novel
  - Short Story/Stories
  - Side Story/Stories
  - Spin-off Series
  - **Fan** Translation
  - **Official** Translation
- Only [supported eBook files](#supported-file-extensions) are copied to the target directory.
  - Non-EPUB eBook files are converted to EPUB using Calibre's `ebook-convert` command.
- Nothing is modified in the source directory.

### Source Folder Structure

- Your eBooks must already be sorted into series folders, the folder name is applied as the series name in the metadata.
- Only specific classification folders are supported, see the above section for the list of them, and the [source code](https://github.com/getBoolean/ebook2kavita/blob/c41f2e5e154e2aaec9584c37f13282e2860d9f6d/ebook2kavita.py#L429) for which exact supported variations.
- eBooks in a non-classification subfolder will still be added, just without a classification.

```txt
Source Folder
├─Series A
│ ├─── **.epub (including subfolders)
│ ├─── <Classification>/**.epub (including subfolders)
│ │   ...
│ Series B
│ │   ...

```

### Example Generated Kavita Series

Generated file structure:

```txt
Target Folder
├─Series A
│ ├─── Series A - v01.epub
│ ├─── Series A Side Story - v01 - <Classification>.epub
│ │   ...
│ Series B
│ │   ...
```

Series in Kavita:

```txt
Series A
├─── Series A, Vol. 1
│   ...
Series A <Classification>
├─── Series A Side Story, Vol. 1
│   ...
Series B
│   ...
```

### Supported File Extensions

Only `epub` has been tested, but these others may work:

- `.epub`
- `.azw4`
- `.azw3`
- `.azw`
- `.chm`
- `.djvu`
- `.docx`
- `.fb2`
- `.htlz`
- `.html`
- `.lit`
- `.lrf`
- `.mobi`
- `.odt`
- `.pdb`
- `.pml`
- `.rb`
- `.rtf`
- `.snb`
- `.tcr`

### Program Output Snippet

```txt
High School Prodigies Have It Easy Even in Another World!:
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:04<00:00,  1.58it/s] 
Holmes of Kyoto:
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 14/14 [00:07<00:00,  1.82it/s] 
Housekeeping Mage from Another World - Making Your Adventures Feel Like Home!:
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 3/3 [00:01<00:00,  1.57it/s] 
How a realist hero rebuilt the kingdom:
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 17/17 [00:10<00:00,  1.57it/s] 
How NOT to Summon a Demon Lord:
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 14/14 [00:16<00:00,  1.16s/it] 
How to Melt the Ice Queen’s Heart:
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  2.16it/s] 
I am Blue, in Pain, and Fragile:
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  1.89it/s] 
I Got A Cheat Ability In A Different World, And Become Extraordinary Even In The Real World:
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 9/9 [00:04<00:00,  1.87it/s] 
I Got a Cheat Skill in Another World and Became Unrivaled in The Real World, Too:
 56%|██████████████████████████████████████████████████████████████████████████▍                                                           | 5/9 [00:02<00:02,  1.97it/s]
```
