import os

DOCS_PREFIX = "docs/modules/ROOT/"
PAGES_PREFIX = DOCS_PREFIX + "pages/"
NAV_PATH = DOCS_PREFIX + "nav.adoc"

LAYOUT_FILE = "nav.layout"

DISTRIBUTIONS = ["enterprise/", "community/"]

PARTIALS = {"Jakarta EE Certification":"jakarta-ee.adoc", 
    "Release Notes":"release-notes.adoc"}

def remove_substring(value:str, substring:str) -> str:
    return str(value).replace(substring, "")


def remove_substrings(value:str, substrings) -> str:
    output = value
    for substring in substrings:
        output = remove_substring(output, substring)
    return output


def make_xref(depth:int, file:str) -> str:
    file_name = file.rpartition("/")
    file_name = file_name[len(file_name)-1]
    file_name = remove_substring(file_name, ".adoc")
    return depth * "*" + " xref:" + file + "[" + file_name + "]"


def make_xref_unlinked(depth:int, name:str) -> str:
    dir_name = name.rpartition("/")
    dir_name = dir_name[len(dir_name)-1]
    return depth * "*" + " " + dir_name


def get_depth(file_path:str) -> int:
    depth = file_path.count("/")
    if(depth == 0):
        return 1
    return depth 


def gen_nav(parent:str, distribution:str) -> list:
    output = []
    
    distribution_specific_parent = os.path.exists(os.path.join(distribution, parent)) and not os.path.exists(parent)
    if(distribution_specific_parent):
        parent = os.path.join(distribution, parent)
    
    for dir, subdirs, files in os.walk(parent, topdown=True):
        relative_dir = remove_substrings(dir, DISTRIBUTIONS)
        relative_dir = remove_substring(relative_dir, PAGES_PREFIX)

        dir_in_distribution = os.path.exists(os.path.join(distribution, dir))
        if(dir_in_distribution and files):
            for dir_file in os.listdir(os.path.join(distribution, dir)):
                files.append(dir_file)

        if(dir != parent):
            output.append(make_xref_unlinked(get_depth(relative_dir), relative_dir))
        if(files):
            for file in files:
                output.append(make_xref(get_depth(os.path.join(relative_dir, file)), os.path.join(relative_dir, file)))

    return output

if __name__ == "__main__":
    for distribution in DISTRIBUTIONS:
        nav = {}

        #Virtually combine directory trees for the base documentation + distribution documentation
        root_dirs = {dir for dir in os.listdir(PAGES_PREFIX)}
        for dir in os.listdir(os.path.join(distribution, PAGES_PREFIX)):
            if dir not in PARTIALS:
                root_dirs.add(dir)

        #Loop through the top level directories
        for set_dir in root_dirs:
            if(os.path.isdir(os.path.join(PAGES_PREFIX, set_dir)) or os.path.isdir(os.path.join(distribution, PAGES_PREFIX, set_dir))):
                nav[set_dir] = gen_nav(os.path.join(PAGES_PREFIX, set_dir), distribution)

        NAV_LOCATION = os.path.join(distribution, NAV_PATH)
        #Clear file contents
        with open(NAV_LOCATION, 'w') as f:
            pass

        with open(LAYOUT_FILE) as layout:
            for value in layout.readlines():
                value = value.strip()
                with open(NAV_LOCATION, 'a') as nav_file:
                    if value in PARTIALS:
                        nav_file.write("\n" + "include::partial$" + PARTIALS[value] + "[]\n")
                        continue
                    nav_file.write( "\n" + value + "\n")
                    for line in nav[value]:
                        nav_file.write(line + "\n")
