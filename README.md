# TAOptimizer - Tiberium Alliances Optimizer

## Purpose
This is a small project to optimize configurations within the multi player online strategy game Tiberium Alliances
Currently it only allows searching for the optimal base layout in term of power production rate.

## How to run
After cloning the repository, create the conda environment running:
conda env create -f environment.yml

Follow these steps:
- Find a specific layout you want to opmtimize in the game
- Load this layout in [CncTaOpt](https://www.cnctaopt.com/) and create a link to it
- Enter that link in main.py, change the number of buildings if necessary (default is 38) and run it
- The Python script will output a new URL, follow it, it shows the optimized layout in CncTaOpt

Hot to run the profiler:
python -m cProfile -o main.profile main.py
python -m pstats main.profile
sort tottime
stats 15