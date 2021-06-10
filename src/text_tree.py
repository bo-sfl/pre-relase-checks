import re
from pathlib import Path
from itertools import islice
from functools import partial
from treelib import tree
import logging
import src.utils as utils

FIND_BRANCH = re.compile(r"\└──|\├──")
FIND_TREE_ELE = re.compile((r"\└|\─|\├|\│"))
MSG = "Please make sure to use '<-' to add description"
class Node_data(object):
    def __init__(self, text):
        self.invalid = False
        self.parse_text(text)

    def parse_text(self, text):
        parts = FIND_TREE_ELE.sub("", text.strip()).split("<")
        if len(parts)==2: # The item has description
            self.item = parts[0].strip()
            self.description = re.sub(r"\-*", "", parts[1]).strip()
        else:
            self.item = parts[0].strip()
            self.description = None
            self.invalid = True


def subtract_project_contents_section(readme_tree, readme_path):
    # Find the Project Contents section
    for node in readme_tree.all_nodes():
        if node.data.clean_text.lower() == "Project Contents".lower():
            contents_root = node
            break
    if not contents_root:
        raise ValueError("Failed to find the project content tree in readme.")
    line_numbers  = sorted([node.identifier for node in 
        readme_tree.subtree(contents_root.identifier).all_nodes()])

    start_line = min(line_numbers)
    end_line = max(line_numbers)
    
    with open(readme_path, 'r') as f:
        contents = f.readlines()

    contents = [(i, contents[i-1]) for i in range(start_line, end_line+1,1)]

    return contents


def find_level(line):
    level = -1
    for m in FIND_BRANCH.finditer(line):
        if level>0:
            raise ValueError("""Failed to parser the Project Content section, \
                please follow the template's format""")
        else:
            level = (m.end()+1)//4
    return level


def parse(readme_tree, readme_path, show=False):
    """
    Given a readme tree to subtract the project contents section and 
    convert it to a tree structure
    """
    max_level = 0
    content_lines = subtract_project_contents_section(readme_tree, readme_path)
    contents = []
    for i, line in content_lines:
        level = find_level(line)
        if level> 0 :
            max_level = level if level > max_level else max_level
            contents.append((i, level, line))

    if max_level == 0 :
        raise ValueError("""Failed to parser the Project Content section, \
                please follow the template's format""")

    # Build tree
    dir_tree = tree.Tree()
    root_line_no = contents[0][0]-1
    dir_tree.create_node('.', root_line_no)  # root node
 
    last_active_lines = [root_line_no] * (max_level + 1)
    last_active_level = 0
    for line_no, level, line in contents:
        parent_level = level-1
        last_active_lines[level] = line_no
        if level>=last_active_level:
            last_active_level = level -1 

        else:
            last_active_level = level

        node_data = Node_data(line)
        
        if node_data.invalid:
            logging.warning(f"Failed in parsering L{line_no}: {line.strip()}")
            logging.warning("This maybe caused by:")
            logging.warning("a) Missing descriptions")
            logging.warning("b) Not using '<-' to add descriptions")
                
        dir_tree.create_node(
            node_data.item,
            line_no, 
            last_active_lines[parent_level], 
            data=node_data,
        )

    if show:
        dir_tree.show(key=lambda node:node.identifier)

    return dir_tree

def tree_as_path_dict(folder_tree):
    path_dict = {}
    for path in folder_tree.paths_to_leaves():
        key = Path(*[folder_tree.get_node(_id).tag for _id in path[1:]])
        path_dict[key]=path[-1]

    return path_dict
        

def check_project_content(readme_folder_tree, folder_tree):
    readme_folder_path_dict = tree_as_path_dict(readme_folder_tree)
    folder_path_dict = tree_as_path_dict(folder_tree)
    for path in folder_path_dict.keys():
        if not readme_folder_path_dict.get(path, None):
            logging.error(
                f"Missing {path} in the Project contexts section. {MSG}"
                )

    for path, line_no in readme_folder_path_dict.items():
        if not folder_path_dict.get(path, None):
            logging.error(
                f"Extra L{line_no}:{path} in the Project contexts section. {MSG}"
                )
