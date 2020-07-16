import argparse
import traceback
import logging
import shutil
from pathlib import Path
from src import folder_tree, markdown_tree, text_tree, syntax_checker, utils


def main(config):
    matser_folder_tree = folder_tree.paser(Path("master"), config, level=5)
    matser_folder_tree.show()

    template_folder_tree = folder_tree.paser(Path("template"), config, level=5)
    
    folder_tree.scan_empty_dirs(matser_folder_tree)
    folder_tree.scan_holdover_items(matser_folder_tree, template_folder_tree)
    
    matser_readme_tree = markdown_tree.paser(utils.get_readme_path('master'))
    template_readme_tree = markdown_tree.paser(utils.get_readme_path('template'))
    markdown_tree.check_readme(matser_readme_tree, template_readme_tree, config)

    # Check unrsolved to~do tags and commented code
    syntax_checker.check_syntax(Path("master"), config)
    matser_readme_folder_tree = text_tree.paser(
        matser_readme_tree, utils.get_readme_path('master'))

    text_tree.check_project_content(
        matser_readme_folder_tree, matser_folder_tree)


if __name__ == "__main__":

    LOG_FILENAME = 'pre_release_check.log'
    logging.basicConfig(filename=LOG_FILENAME,level=logging.WARNING)
    
    try:
        import sys
        sys.path.append("master/.github")
        from pre_release_config import CONFIG
        print("Using the config in .github/pre_release_config.py from the repo")
    except:
        from config import CONFIG
        print("Failed to load the config file from repo")
        print("Using the default config")

    try:
        main(CONFIG)
    except Exception as e:
        logging.exception(e)
        logging.error("The pre-release check failed")
