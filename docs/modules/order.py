import os
import sys

os.chdir(sys.path[0])
nav = ''

file_ext = ".adoc"
start_file = f"loe{file_ext}"

exclusion_list = ["ROOT", "order.py"]
dirs = l3 = [x for x in os.listdir() if x not in exclusion_list]

while dirs:
    dir = f"{dirs.pop()}"
    print(dir)
    path = f"{dir}/pages/"
    files = os.listdir(path)

    if(start_file in files):
        file = f"{path}{files.pop(files.index(start_file))}"
    else:
        continue
    
    title = ' '.join([x.capitalize() for x in dir.split('-')])
    nav += f".{title}\n"

    while files:
        properties = {}
        with open(file, 'r', encoding='utf-8') as open_file:
            for _ in range(5):
                key, value = next(open_file, '').strip("\n").split("=")
                properties[key] = value
    
        nav += f"* xref:{file}[{properties['title']}]\n"
        file = f"{path}{properties['next'].replace('.html', file_ext)}"
        files.remove(file.replace(path, ''))

    with open(f"{dir}/nav.adoc", 'w+', encoding='utf-8') as nav_file:
        nav_file.write(nav)

print(nav)
