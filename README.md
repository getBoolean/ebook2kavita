# jln2kavita

Converts an EPUB folder structure to a Kavita folder structure, adding required metadata and repairing malformed EPUB files.

## Features

- Groups `.epub` files into Kavita series based on subfolders and filenames
- Repair malformed `.epub` files. *(Note: in rare cases this may be very slow)*
- Automatically run Calibre plugin [DeDRM](https://github.com/noDRM/DeDRM_tools) *(only if installed)*

## Requirements

- `Python 3.11+` - `choco install python`
- [Calibre 7+](https://calibre-ebook.com/) and add the installation directory to the `PATH` environment variable
- [tqdm](https://pypi.org/project/tqdm/): `pip install tqdm`

## Usage

1. Clone this repository
1. Open Powershell to the repository directory and run the following command:

```bash
python jln2kavita.py --src "SOURCE_DIR" --target "TARGET_DIR"

# e.g.: python jln2kavita.py --src "B:\Dropbox\Personal\Books\Light Novels, Manga\Just Light Novels" --target "B:\Media Server\Light Novels"
```

## About

- Only EPUB files are copied to the target directory.
- Adds the series name and volume number to the EPUB metadata required by Kavita
  - The series name is the name of the folder containing the EPUB folder plus the classification (see [Source folder structure](#source-folder-structure))
  - The series part number and volume number are extracted from the EPUB filename using regex.
- Classification is determined by the subfolders an EPUB belongs to, case intensitive:
  - Light Novel
  - Web Novel
  - Short Story/Stories
  - Side Story/Stories
  - Spin-off Series
  - **Fan** Translation
  - **Official** Translation

### Source folder structure

```txt
Series A
├─── **.epub (including subfolders)
├─── <Classification>/**.epub (including subfolders)
│   ...
Series B
│   ...

```

### Example generated Kavita series

Generated file structure:

```txt
Series A
├─── Series A - v01.epub
├─── Series A Side Story - v01 - <Classification>.epub
│   ...
Series B
│   ...
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

### Program output snippet

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
