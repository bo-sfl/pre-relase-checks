import hashlib
import logging
from pathlib import Path

def hash_file(f_path):
    m = hashlib.md5()
    with open(f_path, 'rb') as f:
        m.update(f.read())
    return m.hexdigest()

def compare_file(f_path1, f_path2):
    file_1 = hash_file(f_path1)
    file_2 = hash_file(f_path2)
    if file_1 == file_2:
        return True
    else:
        return False

def get_readme_pdf(root):
    pdfs = root.glob('*.pdf')
    for pdf in pdfs:
        if pdf.lower()=="readme.pdf":
            return pdf
    return None

def compare_readme(root):
    new_readme = get_readme_pdf(root)
    old_readme = get_readme_pdf(Path('pdf'))
    if old_readme:
        if compare_file(new_readme, old_readme):
            logging.warning("The main readme PDF is not even with Markdown file")
    else:
        logging.error("Can not find the PDF version of the readme file in the repo")
    