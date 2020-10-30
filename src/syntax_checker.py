import re
import logging
from pathlib import Path

def load_file(f_path):
    try:
        with open(f_path, 'r') as f:
            return [line.strip() for line in f.readlines()]
    except:
        return []

def find_pattern(f_path, prog):
    matches = []
    for i, line in enumerate(load_file(f_path), 1):
        if prog.match(line.lower()):
            matches.append((i, line))
    return matches

def find_todo_tags(root_path):
    file_list = [f for f in Path(root_path).glob('**/*') if f.is_file()]
    file_list = [f for f in file_list 
        if not any(_part.startswith('.') for _part in f.parts)]
    prog_todo = re.compile(r'\#+\s*(todo|to-do|fix-me|fixme)')
    todo_dict = {}
    for file in file_list:
        todos = find_pattern(file, prog_todo)
        if todos and len(todos)>0:
            todo_dict[str(file)] = todos
    return todo_dict

def find_commented_code(root_path):
    file_list = [f for f in Path(root_path).glob('**/*.py')]
    file_list = [f for f in file_list 
        if not any(_part.startswith('.') for _part in f.parts)]
    prog_commented_code = re.compile(r'\#+\s+.*[\+|\-|\*|\/|\(|\=].*')
    commented_code_dict = {}
    for file in file_list:
        commendted_code = find_pattern(file, prog_commented_code)
        if commendted_code and len(commendted_code)>0:
            commented_code_dict[str(file)] = commendted_code
    return commented_code_dict

def check_syntax(root_path, config):
    todo_dict = find_todo_tags(root_path)
    for path, lines in todo_dict.items():
        for line in lines:
            msg = f"{path}: L{line[0]} {line[1]} "
            logging.error(f"Find Unresolved todo at {msg}")

    commendted_code = find_commented_code(root_path)
    ignore_special_lines = set(config['commented_code']['special_lines'])
    for path, lines in commendted_code.items():
        for line in lines:
            if line[1] in ignore_special_lines:
                pass
            else:
                msg = f"{path}: L{line[0]} {line[1]} "
                logging.warning(f"Find commented code at {msg}")