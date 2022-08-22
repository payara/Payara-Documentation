from abc import ABC, abstractmethod
import argparse
import os
import logging
import re

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

FILE_EXTENSION=".adoc"
OVERVIEW_FILE_NAME=f"Overview{FILE_EXTENSION}"

NAV_PATH = DOCS_PREFIX + f"nav{FILE_EXTENSION}"

LAYOUT_FILE = "nav.layout"
PARTIALS = {"Jakarta EE Certification":f"jakarta-ee{FILE_EXTENSION}",
    "Eclipse MicroProfile Certification":f"eclipse-microprofile{FILE_EXTENSION}",
    "Release Notes":f"release-notes{FILE_EXTENSION}",
    "Appendix":f"appendix{FILE_EXTENSION}"}

DISTRIBUTIONS = ['enterprise/', 'community/']

### Classes ###


class _Xobject(ABC):
    '''Abstract acting object for Xdirectory and Xfile. Holds common attributes for both.'''
    _OVERVIEW_ORDINAL = -900
    _UNSORTED_ORDINAL = 900

    def __init__(self, parent, path):
        self.parent = parent
        self.path = path

        self.agnostic_path = self.path
        for substring in DISTRIBUTIONS:
            self.agnostic_path = self.agnostic_path.replace(substring, '')

        self.relative_path = self.agnostic_path.replace(PAGES_PREFIX, '')
        self.file_name = os.path.splitext(os.path.basename(self.path))[0]
        self.depth = self.relative_path.count(os.path.sep)

    @abstractmethod
    def has_children(self) -> bool:
        '''Returns a boolean value if the tree has children.'''

    @abstractmethod
    def get_ordinal(self) -> int:
        '''Returns the ordinal by searching for the 'ord' file in its directory.'''

    @abstractmethod
    def to_xref(self) -> str:
        '''Generates a Antora compliant string for the nav.'''

class Xdirectory(_Xobject):
    '''Tree structure for directories. Adds ability to merge with other trees.
    Ability to get ordinal from the 'ord' file.'''
    _ordinal_regex = "(?<=.ord)\\d+"
    isFile = False
    isDir = not isFile

    def __init__(self, parent, path):
        super().__init__(parent, path)
        self.children = []


    def merge(self, other_directory: 'Xdirectory') -> 'Xdirectory':
        '''The merge function recursively loops through the children of both base
        and the merged tree to create a single tree with all combined children.'''
        if not other_directory:
            return other_directory

        while other_directory.has_children():
            other_child = other_directory.children.pop()
            if other_child.has_children():
                for child in self.children:
                    shared = child.relative_path == other_child.relative_path
                    if shared:
                        child.merge(other_child)
                if not shared and other_child.has_children():
                    self.children.append(other_child)
            else:
                self.children.append(other_child)

        return self


    def has_children(self) -> bool:
        return len(self.children) != 0


    def get_ordinal(self) -> int:
        if os.path.exists(self.path):
            for file in os.listdir(self.path):
                match = re.search(self._ordinal_regex, file)
                if match:
                    return int(match.group().strip())
        return self._UNSORTED_ORDINAL


    def to_xref(self) -> str:
        return f"{self.depth*'*'} {self.file_name}"


class Xfile(_Xobject):
    '''Object representation for file paths on the system. Allows for reading the file
    to extract ordinal.'''
    _ordinal_regex = "(?<=:ordinal:)\\s*\\d+"
    isFile = True
    isDir = not isFile

    def __init__(self, parent, file_path, file_name, file_distribution):
        super().__init__(parent, file_path)
        self.file_name = file_name
        self.distribution = file_distribution
        self._opened = False
        self._ordinal = self._UNSORTED_ORDINAL


    def has_children(self) -> bool:
        return False


    def get_ordinal(self) -> int:
        if self.file_name == OVERVIEW_FILE_NAME:
            return self._OVERVIEW_ORDINAL

        if self._opened is False:
            self._opened = True
            with open(self.path, 'r', encoding="utf-8") as file:
                for _ in range(3):
                    ordinal_string = next(file).strip().replace("-", "\\-")
                    ordinal_match = re.search(self._ordinal_regex, ordinal_string)
                    if ordinal_match:
                        self._ordinal = int(ordinal_match.group().strip())
                        break

        return self._ordinal


    def to_xref(self) -> str:
        return f"{self.depth*'*'} xref:{self.relative_path}[{self.file_name.replace(FILE_EXTENSION, '')}]"


### Functions ###

def get_xfiles(parent:Xdirectory, distribution: str) -> _Xobject:
    '''Recursively traverses the directories and generates Xobjects. 
    Returns the root directory with all children populated.'''

    if os.path.exists(parent.path):
        for file in os.listdir(os.path.normpath(parent.path)):
            filepath = os.path.join(parent.path, file)
            xobject = None

            if os.path.isdir(filepath):
                xobject = get_xfiles(Xdirectory(parent, filepath), distribution)
            elif os.path.isfile(filepath):
                if not bool(re.search(r"\.ord\d+", filepath)):
                    xobject = Xfile(parent, filepath, file, distribution)

            if xobject:
                parent.children.append(xobject)
        return parent
    return None


def sort_xfiles(xobject: Xdirectory) -> Xdirectory:
    '''Calls List Sort on all children recursively'''
    if xobject.has_children():
        xobject.children.sort(key=lambda x: (x.get_ordinal(), x.file_name))
        for child in xobject.children:
            sort_xfiles(child)

    return xobject


def print_tree(tree: Xdirectory) -> str:
    '''Calls to_xref method on all Xobjects recursively'''
    output = []
    if tree:
        if tree.parent:
            output.append(f"{tree.to_xref()}")
        if tree.has_children():
            for child in tree.children:
                output.extend(print_tree(child))
    return output


def gen_nav(parent:str, distribution: str):
    '''Creates two trees, one for the base documentation and another for
    the distribution only documentation. The trees are then merged recursively.'''

    base_files = get_xfiles(Xdirectory(None, parent), 0)
    distribution_files = \
        get_xfiles(Xdirectory(None, os.path.join(distribution, parent)),  distribution)

    files = None   
    if distribution_files:
        files = distribution_files
    elif base_files:
        files = base_files

    if base_files and distribution_files:
        files = base_files.merge(distribution_files)

    sort_xfiles(files)

    return print_tree(files)


if __name__ == "__main__":
    for distribution in DISTRIBUTIONS:
        NAV_LOCATION = os.path.join(distribution, NAV_PATH)
        nav = {}

        logging.debug("Beginning Generation for %s", distribution)

        #Virtually combine directory trees for the base documentation + distribution documentation
        root_dirs = set(os.listdir(os.path.join(distribution, PAGES_PREFIX)))\
            .union(os.listdir(PAGES_PREFIX)).symmetric_difference(PARTIALS)

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
                        logging.info("%s value was replaced by a Partial file in the %s nav.", \
                            value, distribution)
                        continue

                    if value not in nav:
                        logging.warning("%s value was not found in nav. It was skipped instead.",\
                             value)
                        continue

                    nav_file.write(f"\n.{value}\n")

                    for line in nav[value]:
                        if IS_WINDOWS:
                            logging.warning("Windows back slash replaced with forward slash")
                            line = line.replace("\\", "/")
                        nav_file.write(line + "\n")

    logging.info("Generation Complete")