import argparse
import os
import logging

parser = argparse.ArgumentParser()
parser.add_argument( "--log", default="INFO",
    help=(
        "Provide logging level. "
        "INFO | WARNING"
        "Example --log warning', default='INFO'")
)
args = parser.parse_args()
logging.basicConfig(level=args.log.upper())

### Constants ###

IS_WINDOWS = os.name == 'nt'

DOCS_PREFIX = "docs/modules/ROOT/"
PAGES_PREFIX = DOCS_PREFIX + "pages/"

FILE_EXTENSION="adoc"
OVERVIEW_FILE_NAME="Overview.{extension}".format(extension=FILE_EXTENSION)

NAV_PATH = DOCS_PREFIX + "nav.adoc"

LAYOUT_FILE = "nav.layout"
DISTRIBUTIONS = ["enterprise/", "community/"]
PARTIALS = {"Jakarta EE Certification":"jakarta-ee.adoc",
    "Eclipse MicroProfile Certification":"eclipse-microprofile.adoc",
    "Release Notes":"release-notes.adoc"}

### Helpers ###

def remove_substring(value:str, substring:str) -> str:
    return str(value).replace(substring, "")


def remove_substrings(value:str, substrings) -> str:
    output = value
    for substring in substrings:
        output = remove_substring(output, substring)
    return output


def make_xref(depth:int, file:str) -> str:
    file_name = get_name_from_path(file)
    file_name = remove_substring(file_name, ".{0}".format(FILE_EXTENSION))
    return "{fdepth} xref:{fpath}[{fname}]".format(fdepth=depth*"*", fpath=file, fname=file_name)


def make_xref_unlinked(depth:int, name:str) -> str:
    return "{ddepth} {dname}".format(ddepth=depth*"*", dname=get_name_from_path(name))

def get_name_from_path(value:str) -> str:
    value = value.rpartition(os.path.sep)
    return value[len(value)-1]

def get_depth(file_path:str) -> int:
    return file_path.count(os.path.sep)


### Functions ###

def gen_nav(parent:str, distribution:str) -> list:
    output = []
    #Bool value to determine if the parent directory exists only in the distribution specific documentation
    if(not os.path.exists(parent)):
        parent = os.path.join(distribution, parent)
    
    for dir, subdirs, files in os.walk(parent, topdown=True):
        relative_dir = remove_substrings(dir, DISTRIBUTIONS + [PAGES_PREFIX])

        logging.debug("Relative Directory {0}".format(relative_dir))

        dirstribution_dir_path = os.path.join(distribution, dir)
        if(os.path.exists(dirstribution_dir_path)):
            files += os.listdir(dirstribution_dir_path)

        logging.debug("Files {0}".format(files))

        #Avoid writing root title as unlinked xref
        if(dir is not parent):
            output.append(make_xref_unlinked(get_depth(relative_dir), relative_dir))
        if(files):
            #Put all Overview files to the beginning order
            if OVERVIEW_FILE_NAME in files:
                files.insert(0, files.pop(files.index(OVERVIEW_FILE_NAME)))
            for file in files:
                if file.endswith(FILE_EXTENSION):
                    joint_path = os.path.join(relative_dir, file)
                    output.append(make_xref(get_depth(joint_path), joint_path))

    return output

if __name__ == "__main__":
    for distribution in DISTRIBUTIONS:
        nav = {}

        logging.debug("Beginning Generation for {0}".format(distribution))

        #Virtually combine directory trees for the base documentation + distribution documentation
        root_dirs = set(os.listdir(os.path.join(distribution, PAGES_PREFIX))).symmetric_difference(PARTIALS).union(os.listdir(PAGES_PREFIX))

        logging.debug("Root directories {0}".format(root_dirs))

        #Loop through the top level directories
        for set_dir in root_dirs:
            dir_path = os.path.join(PAGES_PREFIX, set_dir)
            if(os.path.isdir(dir_path) or os.path.isdir(os.path.join(distribution, dir_path))):
                nav[set_dir] = gen_nav(dir_path, distribution)

        NAV_LOCATION = os.path.join(distribution, NAV_PATH)
        
        #Clear file contents
        with open(NAV_LOCATION, 'w') as f:
            pass

        with open(LAYOUT_FILE) as layout:
            for value in layout.readlines():
                value = value.strip()
                with open(NAV_LOCATION, 'a') as nav_file:
                    if value in PARTIALS:
                        nav_file.write("\ninclude::partial${partial}[]\n".format(partial=PARTIALS[value]))
                        logging.info("{0} value was replaced by a Partial file in the {1} nav.".format(value, distribution))
                        continue

                    if value not in nav:
                        logging.warning("{0} value was not found in nav. It was skipped instead.".format(value))
                        continue
                    
                    nav_file.write( "\n.{title}\n".format(title=value))
                    
                    for line in nav[value]:
                        if IS_WINDOWS:
                            logging.warning("Windows back slash replaced with forward slash")
                            line = line.replace("\\", "/")
                        nav_file.write(line + "\n")

    logging.info("Generation Complete")
