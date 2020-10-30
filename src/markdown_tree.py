import re
import hashlib
from pathlib import Path
from itertools import islice
from functools import partial
from treelib import tree
import logging
import src.utils as utils


def parse(f_path: Path, show: bool=False):
    """
    Given a markdown file path to parse a doc tree
    The file's hierarchy is determined by heading hierarchy.
    eg. `# `, `## ` and `### ` etc
    """
    # Use line 0 as root
    text_tree = tree.Tree()
    text_tree.create_node('Root', 0, data=Node_data('# 0. Root'))  # root node

    # Find the lowerest heading level
    markdown_contents = [Node_data(line) for line in utils.read_file(f_path)]
    max_level = max([node_data.level for node_data in markdown_contents])

    if max_level == 0 :
        # Case of no heading found
        raise ValueError("Can not find any heading in the Readme file.")
    
    # Build tree
    last_active_lines = [0] * (max_level + 1)
    last_active_level = 0
    for line_no, node_data in enumerate(markdown_contents, 1):
        if node_data.is_heading:
            # Heading line
            last_active_lines[node_data.level] = line_no
            last_active_level = node_data.level
            line_level = last_active_level-1
        else:
            line_level = last_active_level
        
        text_tree.create_node(
            node_data.raw_text, 
            line_no, 
            last_active_lines[line_level], 
            data = node_data,
        )
            
    if show:
        text_tree.show(key=lambda node:node.identifier)
    
    return text_tree


IS_HEADING = re.compile(r"^\#*\s")
FIND_NUMBER = re.compile(r"^[\d+\.]+[\d+|\d+\.](?=\s)")

class Node_data(object):
    def __init__(self, text):
        self.level= -1
        self.number = None
        self.clean_text = None
        self.is_heading = False
        self.raw_text = text
        self.parse_text(text)

    def parse_text(self, text):
        """
        Convert a line to a data class
        Extract heading level, number and body for a heading line.
        """
        is_heading = IS_HEADING.search(text)
        if is_heading:
            self.is_heading = True
            self.level = len(is_heading.group(0).strip())
            heading_text = text[self.level:].strip()
            heading_text = heading_text.split('(')[0].strip()
            number_match = FIND_NUMBER.match(heading_text)
            if number_match:
                self.number = number_match[0]
                self.clean_text = heading_text[len(self.number):].strip()
            else:
                self.clean_text = heading_text
        else:
            self.clean_text = text


def check_heading_number(tree, config):
    """Check if a heading is number"""
    unnumbered_heading = set(config['readme']["unnumbered_heading"])
    for node in tree.all_nodes():
        if node.data.is_heading and \
           node.data.number is None and \
           node.data.level>1 and \
           node.data.level<4 and \
           node.data.clean_text not in unnumbered_heading:
           logging.warning(f"Heading line {node.data.clean_text} is not numbered")

def check_heading_order(tree, config):
    """Check if the heading number is ordered"""
    ordered_node = sorted([(node.identifier, node.data.number)
        for node in tree.all_nodes()
        if node.data.number
    ])
    re_ordered_node = sorted(ordered_node, key=lambda x : x[1])
    for (id1, _), (id2, _) in zip(ordered_node, re_ordered_node):
        if id1 != id2:
            line = tree.get_node(id1).tag
            logging.error(f"L{id1} {line} is not numbered correctly")

def find_last_heading(text, sign = "#"):
    for i, char in enumerate(text):
        if char != "#":
            break
    return i

is_heading = lambda node:node.data.level>0

is_text = lambda node:node.data.level<0
            
def heading_texts(nodes):
    node_texts = []
    for node in nodes:
        tag = node.tag
        heading = tag[find_last_heading(tag):].strip()
        if "(" in heading:
            # If there is a description inside parentheses, remove it
            heading = heading.split("(")[0].strip()
        node_texts.append(heading)
    
    return set(node_texts)


def line_texts(nodes):
    node_texts = {}
    for node in nodes:
        if node.tag:
            node_texts[node.identifier] = node.tag
    return node_texts

def check_readme(master_readme, template_readme, config):
    check_heading_number(master_readme, config)
    check_heading_order(master_readme, config)
    # Check mandatory sections
    mandatory_sections = set(config['readme']['mandatory_sections'])
    master_headings = heading_texts(list(master_readme.filter_nodes(is_heading)))
    for section in mandatory_sections:
        if section not in master_headings:
            logging.error(f"Missing a mandatory section in README.md: {section}")

    # Check mandatory headings
    mandatory_headings = set(config['readme']['mandatory_headings'])
    for heading in mandatory_headings:
        if heading not in master_headings:
            logging.error(f"Missing a mandatory section in README.md: {heading}")

    # Check mandatory texts
    mandatory_lines = utils.parser_line_no(config['readme']['mandatory_lines'])
    mandatory_lines = {template_readme.get_node(i).tag: i for i in mandatory_lines}
    master_text = line_texts(list(master_readme.filter_nodes(is_text)))
    
    for line, i in mandatory_lines.items():
        if line not in set(master_text.values()):
            logging.error(f"Missing a mandatory line in README.md: L{i} :{line}")

    # Check duplicate texts
    template_text = line_texts(list(template_readme.filter_nodes(is_text)))
    ignore_lines = utils.parser_line_no(config['readme']['ignore_lines'])
    reduce_template_text = {i:line for i, line in template_text.items() if i not in ignore_lines}
    for i, line in master_text.items():
        if line in set(reduce_template_text.values()):
            if line in mandatory_lines:
                pass
            else:
                logging.error(f"Find a exact line from template README.md: L{i} :{line}")

