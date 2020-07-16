
import re
import hashlib
import logging
from pathlib import Path
from itertools import islice
from functools import partial
from treelib import tree


def tree_clean_up(contents: list, exclude_filenames: list, exclude_paths: list):
    contents = [_x for _x in contents \
        if not any(re.match(_pattern, _x.parts[-1]) for _pattern in exclude_filenames)]
    contents = [_x for _x in contents \
        if not any(str(_x).endswith(_path) for _path in exclude_paths)]
    return sorted(contents)


def paser(
    dir_path: Path, config : dict, 
    level: int=-1, limit_to_directories: bool=False,
    ):
    """Given a directory Path object to parse a tree structure"""

    clean_up =partial(
        tree_clean_up,
        exclude_filenames = config['folder_analysis']['exclude_filenames'], 
        exclude_paths = config['folder_analysis']['exclude_paths'])

    dir_tree = tree.Tree()
    dir_tree.create_node('.', dir_path)  # root node

    def inner(dir_path: Path, level=-1):
        if not level: 
            return # 0, stop iterating
        if limit_to_directories:
            contents = [d for d in dir_path.iterdir() if d.is_dir()]
        else: 
            contents = list(dir_path.iterdir())
        contents = clean_up(contents)
        for path in contents:
            if path.is_dir():
                dir_tree.create_node(str(path.parts[-1]), path, path.parent)
                yield 
                yield from inner(path, level=level-1)
            elif not limit_to_directories:
                dir_tree.create_node(str(path.parts[-1]), path, path.parent)
                yield

    _ = list(inner(dir_path, level=level))
    hash_tree(dir_tree)

    return dir_tree

class Node_data(object):
    def __init__(self, hash_value, is_empty_dir):
        self.hash = hash_value
        self.is_empty_dir = is_empty_dir
        
def hash_tree(tree):
    root = tree.get_node(tree.root)
    if root.is_leaf():
        hash_leaf(root)
    else:
        m = hashlib.sha256()
        is_empty_dir = True
        for child in tree.children(root.identifier):
            hash_tree(tree.subtree(child.identifier))
            m.update(str.encode(child.data.hash))
            is_empty_dir = is_empty_dir & child.data.is_empty_dir
        root.data = Node_data(m.hexdigest(), is_empty_dir)
            
def hash_leaf(node):
    if node.identifier.is_file():
        node.data = Node_data(hash_file(node.identifier), False)
    else:
        # Empty folder
        node.data = Node_data(hashlib.sha256(b"empty").hexdigest(), True)

def hash_file(f_path):
    m = hashlib.sha256()
    f = open(f_path, 'rb')
    for _ in range(1000):
        # Read file in as little chunks, up to 4 MB
        buf = f.read(4096)
        if not buf : break
        m.update(buf)
    f.close()
    return m.hexdigest()


def tree_as_dict(folder_tree):
    node_dict = {}
    for node in folder_tree.all_nodes():
        str_path = str(get_relative_path(folder_tree, node))
        hash_vale = node.data.hash
        node_dict[str_path] = hash_vale
    return node_dict


def scan_empty_dirs(folder_tree):
    for node in folder_tree.all_nodes():
        if node.data.is_empty_dir:
            path_name = get_relative_path(folder_tree, node)
            if list(node.identifier.glob("**/.gitkeep")):
                pass
            else:
                logging.error(f'Found a empty directory: {path_name}')


def get_relative_path(folder_tree, node):
    return node.identifier.relative_to(folder_tree.root)


def scan_holdover_items(matser_folder_tree, template_folder_tree):
    matser_folder_dict = tree_as_dict(matser_folder_tree)
    template_folder_dict = tree_as_dict(template_folder_tree)
    for str_path, hash_value in matser_folder_dict.items():
        if hash_value == template_folder_dict.get(str_path, 'None'):
            logging.error(f'Found a holdover item from template : {str_path}')