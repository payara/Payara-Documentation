import argparse
import os
import logging

parser = argparse.ArgumentParser()
parser.add_argument( "--log", default="INFO",
    help=(
        "Provide logging level. "
        "INFO | WARNING | DEBUG"
        "Example --log warning', default='INFO'")
)
args = parser.parse_args()
logging.basicConfig(level=args.log.upper())

### Constants ###

IS_WINDOWS = os.name == 'nt'

DOCS_PREFIX = "docs/modules/ROOT/"
PAGES_PREFIX = DOCS_PREFIX + "pages/"

FILE_EXTENSION="adoc"
OVERVIEW_FILE_NAME=f"Overview.{FILE_EXTENSION}"

NAV_PATH = DOCS_PREFIX + f"nav.{FILE_EXTENSION}"

LAYOUT_FILE = "nav.layout"
PARTIALS = {"Jakarta EE Certification":f"jakarta-ee{FILE_EXTENSION}",
    "Eclipse MicroProfile Certification":f"eclipse-microprofile{FILE_EXTENSION}",
    "Release Notes":f"release-notes{FILE_EXTENSION}",
    "Appendix":f"appendix{FILE_EXTENSION}"}

### Helpers ###

def remove_substring(string:str, substring:str) -> str:
    '''Removes a provided substring from a string. Returns the result.'''

    return str(string).replace(substring, "")


def remove_substrings(string:str, substrings) -> str:
    '''Removes a list of substrings from a single string. Returns the result.'''

    output = string
    for substring in substrings:
        output = remove_substring(output, substring)
    return output


def make_xref(depth:int, file:str) -> str:
    '''Creates a formatted Xref line from the filepath and filename.'''

    file_name = remove_substring(get_path_subsection(file, 1), f".{FILE_EXTENSION}")
    return "{fdepth} xref:{fpath}[{fname}]".format(fdepth=depth*"*", fpath=file, fname=file_name)


def make_xref_unlinked(depth:int, name:str) -> str:
    '''Makes a formatted unlinked Xref line from the filepath and filename.'''

    return "{ddepth} {dname}".format(ddepth=depth*"*", dname=get_path_subsection(name, 1))


def get_path_subsection(string:str, index:int) -> str:
    '''Divides the filepath string based on the os.path.sep value. Returns the value at the requested index.'''

    subsection = string.rpartition(os.path.sep)
    return subsection[len(subsection)-index]


def get_depth(file_path:str) -> int:
    '''Counts the number of os.path.sep, which will be the depth of the file in the file structure.'''

    return file_path.count(os.path.sep)

### Functions ###

def get_tree(parent:str) -> dict:
    '''Returns a depth-first tree of the directory path as the key, and the list of files as the value. Parent is the root of the tree.'''

    tree = {}

    for root, _, files in os.walk(parent, topdown=True):
        if(files and OVERVIEW_FILE_NAME in files):
            index = files.index(OVERVIEW_FILE_NAME)
            if(index != 0):
                logging.debug("Moved Overview file for %s to the top of the directory", root)
                files.insert(0, files.pop(files.index(OVERVIEW_FILE_NAME)))
        tree[root] = files

    return tree

def gen_nav(parent:str, distribution:str):
    '''Creates two trees, one for the base documentation and another for the distribution only documentation.
    It attempts to insert the distribution only files into the base documentation, if that is not possible it will move up one 
    directory until it finds a shared file path. Otherwise it will print at the same path the file exists in the distribution specific documentation, as 
    it is then considered unique to the distribution and should be included.
    
    It then generates the Xref values to be printed into the nav.'''

    output = []

    tree = get_tree(parent)
    distribution_tree = get_tree(os.path.join(distribution, parent))

    key_list = list(tree)
    
    for key in distribution_tree:
        agnostic_path = remove_substring(key, distribution)
        if agnostic_path in key_list:
            continue
        
        dir_up = agnostic_path
        while(dir_up and dir_up not in key_list):
            dir_up = get_path_subsection(dir_up, 3)

        if(dir_up):
            key_list.insert(key_list.index(dir_up)+1, agnostic_path)
            continue

        key_list.append(agnostic_path)
                
    for key in key_list:
        relative_path = remove_substrings(key, [PAGES_PREFIX, distribution])
        if(parent != key):
            output.append(make_xref_unlinked(get_depth(relative_path), key))
        if(key in tree):
            for value in tree[key]:
                output.append(make_xref((get_depth(relative_path)+1), os.path.join(relative_path, value)))
        
        distribution_key = os.path.join(distribution, key)
        if(distribution_key in distribution_tree):
            for value in distribution_tree[distribution_key]:
                output.append(make_xref((get_depth(relative_path)+1), os.path.join(relative_path, value)))

    return output

if __name__ == "__main__":
    for distribution in DISTRIBUTIONS:
        NAV_LOCATION = os.path.join(distribution, NAV_PATH)
        nav = {}

        logging.debug("Beginning Generation for %s", distribution)

        #Virtually combine directory trees for the base documentation + distribution documentation
        root_dirs = set(os.listdir(os.path.join(distribution, PAGES_PREFIX))).symmetric_difference(PARTIALS).union(os.listdir(PAGES_PREFIX))

        logging.debug("Root directories %s", root_dirs)

        #Loop through the top level directories
        for set_dir in root_dirs:
            dir_path = os.path.join(PAGES_PREFIX, set_dir)
            if(os.path.isdir(dir_path) or os.path.isdir(os.path.join(distribution, dir_path))):
                nav[set_dir] = gen_nav(dir_path, distribution)
        
        #Clear file contents
        with open(NAV_LOCATION, 'w', encoding="utf-8") as _:
            pass

        with open(LAYOUT_FILE, encoding="utf-8") as layout:
            for value in layout.readlines():
                value = value.strip()                
                with open(NAV_LOCATION, 'a', encoding="utf-8") as nav_file:
                    if value in PARTIALS:
                        path = PARTIALS[value]
                        nav_file.write(f"\ninclude::partial${path}[{value}]\n")
                        logging.info("%s value was replaced by a Partial file in the %s nav.", value, distribution)
                        continue

                    if value not in nav:
                        logging.warning("%s value was not found in nav. It was skipped instead.", value)
                        continue
                    
                    nav_file.write(f"\n.{value}\n")
                    
                    for line in nav[value]:
                        if IS_WINDOWS:
                            logging.warning("Windows back slash replaced with forward slash")
                            line = line.replace("\\", "/")
                        nav_file.write(line + "\n")

    logging.info("Generation Complete")
