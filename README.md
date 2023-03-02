# TAOptimizer - Tiberium Alliances (Power) Optimizer

## Purpose
This is a small project to optimize configurations within the multi player online strategy game Tiberium Alliances.
Currently it only allows searching for the optimal base layout in terms of power production rate. But the code could easily be extended to optimize for other parameters.

## How to use
If you're using Conda, you can create the proper environment running:

`conda env create -f environment.yml`

Then essentially run main.py, changing the parameters depending on what you want.
Two types searches are supported:

1) Optimize a single layout given by a [CncTaOpt](https://www.cnctaopt.com/)-link
2) Optimize all layouts given by a screenshot from the TA-BaseScanner script. Here is an example of the input/output:

![source image](./sample_layouts.png "source")
->
![resulting image](./sample_layouts_out.png "target")

There are two parameters for these searches:

- *n_buildings*: the number of buildings to place (accumulators + accus). 38 by default, leaving 2 space for the defense buildings
- *top_n*: at every step (i.e. after placing an accumulator), the algorithm checks for every empty field how much the overall rate can be improved by placing an accu there. The fields are sorted descending by this 'potential' improvement. The top_n ranks in the sorted list are then used for the next recursion. By default top_n = 1 only takes the best field (or fields, if there are multiple with the same rate). This is very fast (much less than a second), but does not always return the optimal solution. Top_n = 2 seems to return the best solution (always?), but takes multiple seconds.

## Open Points
At the moment the search is a simple brute force depth-first search. This is too slow to find the guaranteed optimal solution in reasonable time. It seems that by setting the top_n parameter to 2, optimal solutions are returned. However, even this is slow and there could be a case where it doesn't return the optimal solution. Using an A* search might be faster, but finding a good (and admissible) heuristic for this problem is not trivial.

Further improvement of the existing code can be done by focusing on tuning the key functions. 
Profiling can be generated like this:

````
python -m cProfile -o main.profile main.py
python -m pstats main.profile
sort tottime
stats 15
````