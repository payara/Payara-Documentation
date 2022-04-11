import os

### Constants ###

DOCS_PREFIX = "docs/modules/ROOT/"
PAGES_PREFIX = DOCS_PREFIX + "pages/"
NAV_PATH = DOCS_PREFIX + "nav.adoc"
LAYOUT_FILE = "nav.layout"
DISTRIBUTIONS = ["enterprise/", "community/"]
PARTIALS = {"Jakarta EE Certification":"jakarta-ee.adoc", 
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
    file_name = remove_substring(file_name, ".adoc")
    return "{fdepth} xref:{fpath} [{fname}]".format(fdepth=depth*"*", fpath=file, fname=file_name)


def make_xref_unlinked(depth:int, name:str) -> str:
    return "{ddepth} {dname}".format(ddepth=depth*"*", dname=get_name_from_path(name))

def get_name_from_path(value:str) -> str:
    value = value.rpartition("/")
    return value[len(value)-1]

def get_depth(file_path:str) -> int:
    return file_path.count("/")


### Functions ###

def gen_nav(parent:str, distribution:str) -> list:
    output = []
    
    #Bool value to determine if the parent directory exists only in the distribution specific documentation
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

        #Avoid writing root title as unlinked xref
        if(dir != parent):
            output.append(make_xref_unlinked(get_depth(relative_dir), relative_dir))
        if(files):
            #Put all Overview files to the beginning order
            if "Overview.adoc" in files:
                files.insert(0, files.pop(files.index("Overview.adoc")))
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
                        nav_file.write("\n" + "include::partial${partial}".format(partial=PARTIALS[value]) + "[]\n")
                        continue
                    nav_file.write( "\n.{title}\n".format(title=value))
                    for line in nav[value]:
                        nav_file.write(line + "\n")
