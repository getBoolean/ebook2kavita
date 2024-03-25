# jln2kavita

Converts a JLN folder structure to a Kavita folder structure so that EPUBS can be indexed by Kavita, and adds the series name and
volume number to the EPUB metadata to ensure it groups and sorts correctly.

## Features

- Groups `.epub` files into series based on series name, year/part #, short stories, web/light novel,
and fan/official translation.
- Repair malformed `.epub` files. (Note, in rare cases this may take a long time.)
- Automatically runs Calibre's `DeDRM` plugin if it is installed.

## Usage

```bash
# Source -> Target
python .\jln2kavita.py "B:\Dropbox\Personal\Books\Light Novels, Manga\Just Light Novels" "B:\Media Server\Light Novels"
```

## Requirements

- Python 3.11+
- Calibre 6
- [tqdm](https://pypi.org/project/tqdm/) (`pip install tqdm`)

## About

- This script converts the JLN folder structure to a Kavita folder structure.
- Only EPUB files are copied to the target directory.
- Adds the series name and volume number to the EPUB metadata to ensure it groups and sorts correctly.
  - The series name added is the name of the folder containing the EPUB folder (see `Supported folder structures:`).
  - The volume number/index is extracted from the EPUB filename using regex.
- Subfolders (with the exception of folders that contain "official") are ignored, so spinoffs might be missed. This is intentional, and won't be fixed.
If all subfolders were included, both fan translations and official translations could be copied to the target directory.
  - If you identify any spinoffs it missed, you can manually copy it to the series `Specials` folder in the target directory.
- It tries to prioritize official translations over fan translations. If the official translation folder is found, the fan translation isn't copied.
  - If you want the fan translations, you can manually copy them to the series folder in the target directory or create a separate series folder for it.

JLN folder structure:

```txt
Series A
├───EPUB
│       Series A - 01.epub
│       ...
├───PDF
│       Series A - 01.pdf
│       ...
Series B
│   ...

```

Kavita folder structure:

```txt
Series A
│   Series A - 01.epub
│   ...
Series B
│   ...
```

Program output snippet:

```txt
High School Prodigies Have It Easy Even in Another World!:
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:04<00:00,  1.58file/s] 
Holmes of Kyoto:
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 14/14 [00:07<00:00,  1.82file/s] 
Housekeeping Mage from Another World - Making Your Adventures Feel Like Home!:
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 3/3 [00:01<00:00,  1.57file/s] 
How a realist hero rebuilt the kingdom:
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 17/17 [00:10<00:00,  1.57file/s] 
How NOT to Summon a Demon Lord:
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 14/14 [00:16<00:00,  1.16s/it] 
How to Melt the Ice Queen’s Heart:
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  2.16file/s] 
I am Blue, in Pain, and Fragile:
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  1.89file/s] 
I Got A Cheat Ability In A Different World, And Become Extraordinary Even In The Real World:
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 9/9 [00:04<00:00,  1.87file/s] 
I Got a Cheat Skill in Another World and Became Unrivaled in The Real World, Too:
 56%|██████████████████████████████████████████████████████████████████████████▍                                                           | 5/9 [00:02<00:02,  1.97file/s]
```
