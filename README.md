# jln2kavita

Converts a JLN folder structure to a Kavita folder structure. Only EPUB files are copied to the target directory. It also adds the series name and
series index to the EPUB metadata using Calibre. It tries to prioritize official translations over fan translations. If the official translation is found, the fan translation isn't copied.

## Usage

```bash
# Source -> Target
python .\jln2kavita.py "B:\Dropbox\Personal\Books\Light Novels, Manga\Just Light Novels" "B:\Media Server\Light Novels"
```

## Requirements

- Python 3
- Calibre

## About

This script converts the JLN folder structure to a Kavita folder structure. Only EPUB files are copied to the target directory. The series name added to the EPUB metadata
is the name of the folder containing the EPUB folder. The series index is extracted from the EPUB filename using regex.

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
