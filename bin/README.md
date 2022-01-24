This is a contiunation of [user670/eCDP-translation](https://github.com/user670/eCDP-translation). `.bin` files in eCDP are files that contain texts mainly used in SOC Guides and Self Check.

# Text files
Text files in this repo are texts found in the game's files, converted from binary to readable files using the scripts in the scripts folder.

One text file may contain multiple pieces of text; they are separated by `===#===`.

# Scripts
There are two Python 3 scripts in the scripts folder.

parse.py takes all files in `./original`, converts them into txt files, and put them in `./txt`.

builder.py takes all files in `./txt`, converts them back into binary, and put them in `./modified`.

The script doesn't traverse folders within the folders (and treats them as if files, and potentially throw errors). Contributions that implement traversing folders within the folders are more than welcome.
