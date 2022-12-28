# eCrew Development Program (eCDP) English Translation
This is a repository to create a fan English translation patch of McDonald's [eCrew Development Program](https://en.wikipedia.org/wiki/ECrew_Development_Program).

## Repository Structure
The repository consists of three sections, one directory for each section:
- `overlay` - Translates overlay files, which contain UI texts, as well as the game's compiled code.
- `bin` - Translates bin files, containing texts mainly for SOC Guides and Self Check.
- `cmcd` - Translates the "Challenge the McDonald's" section. Also replaces the font used there.

## Patching your ROM
This guide is for patching all translations to your ROM. For patching individual sections, please check instructions inside corresponding directories.
1. Install Python 3.9 on your computer, and install `ndspy` package:
```
pip install ndspy
```
2. Place an original, unmodified ROM of McDonald's eCDP in this directory. (File SHA-1: `136aacc9d3d7c8567381cd4e735ff3c004a018d0`)
4. Run `patch.py` in Python 3.9 (Not tested with other versions) with the ROM file specified:
```
python patch.py <ROM Filename>.nds
```
4. The script will patch strings of all sections, and it will create a file named `\<ROM Filename\>-patched.nds`.
5. Patching done! You can now play the game in a Nintendo DS emulator of your choice.
