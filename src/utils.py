import json
from pathlib import Path
def parser_line_no(values:list):
    line_nos = []
    for value in values:
        if isinstance(value, int):
            line_nos.append(value)
        elif isinstance(value, str):
            start, end = value[1:].split('-')
            line_nos.extend(list(range(int(start), int(end)+1)))
        else:
            raise ValueError("Encounter error")
    return set(line_nos)


def read_file(f_name):
    with open(f_name, 'r') as f:
        texts = [line.strip() for line in f.readlines()]
    return texts

def read_json(f_name):
    with open(f_name, 'rb') as f:
        content = json.load(f)
    return dict(content)

def get_readme_path(root):
    for file in Path(root).glob('*'):
        if file.is_file() and file.parts[-1].lower() == "readme.md":
            break
    return file
