# jln2kavita

Converts a JLN folder structure to a Kavita folder structure. Only EPUB files are copied to the target directory. It also adds the series name and
series index to the EPUB metadata using Calibre.

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
