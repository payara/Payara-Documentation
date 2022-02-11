#!/bin/bash

#--- README ---
# This script will generate a nav file for Antora using the physical file structure of the files.
# Folders will act as drop downs.
# Files in folders will be children to those dropdowns.
# Files will have the same name, including punctuation as the file name.

# To use this script, place it in the same folder as the 'pages' directory
# For example: payara-community-documentation/docs/modules/ROOT/

#--- CONSTANTS ---

# You do not need to change this unless the script is in a different directory
readonly WORKING_DIR="$(pwd)/pages"

# The output name of the nav file, this should be the same as configured in antora.yml
readonly NEW_NAV_FILE_NAME="nav.adoc"

# The output location of the nav file, by default it will be in the same directory as the script.
readonly OUTPUT_NAV_LOCATION="$(pwd)/$NEW_NAV_FILE_NAME"

#--- SETUP ---

rm $OUTPUT_NAV_LOCATION
touch $OUTPUT_NAV_LOCATION

cd $WORKING_DIR

#--- FUNCTIONS ---

# Parameters: Parent directory for formatting
# This function is responsible for writing to the nav at appropriate points
write_to_nav() {
    readarray -t dirs < <(find . -type d -printf '%P\n')

    for dir in "${dirs[@]}"; do
        readarray -t files_to_sort < <(find "$dir" -maxdepth 1 -type f)
        #If there is only one directory, it is the one we currently are in, so we search in it.
        if [[ ${#dirs[@]} -eq 1 ]]; then
            readarray -t files_to_sort < <(find * -maxdepth 1 -type f)
        fi

        #If directory is not a empty string, write it to the nav
        if [[ ! -z $dir ]]; then
            #Add parent folder to root of the path
            dir="${1}/$dir"

            echo "$(construct_line "$dir")" >> $OUTPUT_NAV_LOCATION
        fi

        #Sort then write files in directory seperate from writing the directory to nav
        if [[ ${#files_to_sort[@]} -ne 0 ]]; then
            sort_files "$dir"
            for file in "${sorted_files[@]}"; do
                file="$1/$file"

                echo "$(construct_line "$file")" >> $OUTPUT_NAV_LOCATION
            done
        fi
    done
}


# Parameters: List of .adoc files
# Sorts files according to the 'Ordinal' attribute in the page
sort_files() {
    local ordinal_list=()

    for file in "${files_to_sort[@]}"; do
        ordinal_list+=("$(get_ordinal "$file"):::$file")
    done

    #We want to delimit based on new line, not the default space
    SAVEDIFS=$IFS
    IFS=$'\n'
    sorted_files=($(
        for KEY in "${ordinal_list[@]}"; do
            echo "$KEY"
        done | sort -r | awk -F::: '{print $2}'
    ))
    IFS=$SAVEDIFS
}

# Parameters The path to the directory which depth is calculated from and filename is taken from
# This function is responsible for creating the line that will be appended into the nav file
construct_line() {
    local file=$1
    local depth=$(get_depth "$file")
    local filename=$(get_filename "$file")
    local stars=$(printf "%"$depth"s")
    echo "${stars// /*} xref:${file}[${filename}]"
}

# Parameters: The path to the file
# Counts the number of '/' which represents the depth of the file in subfolders
get_depth() {
    echo "$(grep -o '/' <<< $1 | grep -c .)"
}

# Parameters: The path of the file
# Returns just the filename without file extension or path
get_filename() {
    local path=$1
    filename=${path##*/}
    filename=${filename%.adoc}
    echo $filename
}

# Parameters: File path
# Returns the ordinal value that is present in the :ordinal: attribute in the page.
get_ordinal() {
    if [[ ! -f $1 ]]; then
        echo 0
        return
    fi
    content=$(cat "$1")

    regex=":ordinal: ([[:digit:]]+)"
    if [[ $content =~ $regex ]]; then
        echo ${BASH_REMATCH[1]}
    else
        echo 0
    fi
}

#--- MAIN ---

#Loops through directories in the WORKING_DIR and constructs a nav from them.
for dir in */ ; do
    dir=${dir%?}
    cd "${dir}"
    echo >> $OUTPUT_NAV_LOCATION
    echo ".$dir" >> $OUTPUT_NAV_LOCATION
    write_to_nav "$dir"
    cd $WORKING_DIR
done