# Overlay Translation
## Ooutdated Instructions - Will be updated later

## How to apply the translations
1. Place the original unmodified eCDP ROM in this folder, and rename it to `ecdp.nds` or use the command line argument `-r` or `--romname` to read the name of the rom.
2. Run the python script `patch.py`.
3. Wait for the patching process to complete.
4. A file named `ecdp_patched.nds` should appear. You can now play the ROM in any DS emulator of your choice.

## Requirements
- Python version must be higher than 3.8.10. (3.9.0 is recommended)
- You must install `ndspy` package before running the script. (Type `pip install ndspy`)

## Additional Notes
Original python scripts from [EliCrystal2001/nds-string-editor](https://github.com/EliCrystal2001/nds-string-editor). This repository uses a modified version of the script.
