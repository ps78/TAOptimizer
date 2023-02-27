from game_mechanics import BaseLayout, Constants
from collections import namedtuple
import numpy as np

class PathNode:    
    """
    Type used for elements of solution paths in SolutionItem.path
    """
    def __init__(self, coord, power_rate :int):
        self.coord = coord
        self.power_rate = power_rate
    
    def __str__(self):
        return f"({self.coord[0]},{self.coord[1]}) - {self.power_rate:,}/h"

class SolutionItem:
    """
    Type used for elements returned in the solution list by search
    """
    def __init__(self, power_rate :int, path :list[PathNode]):
        self.power_rate = power_rate
        self.path = path

    def __str__(self):
        s = f"Solution with {len(self.path)} accus, power rate: {self.power_rate:,}\n"
        for node in self.path:
            s += f"   {node}\n"
        return s

def get_top_n_ranks(lst :list, top_n :int, selector = None) -> list:
    """
    Function which which returns the top_n ranked elements from the list lst.
    Every rank is counted as one element, 
    e.g. for a list (4,5,5,3) with top_n=2 it returns (5,5,4)
    Selector is an optional function to select the value from a list item to be used
    for comparison

    Parameters:
    - lst:      list of items
    - top_n:    number of top ranks to return
    - selector: optional function that takes one list element and returns a number
                which is then used for calculating the rank
    """
    lst.sort(reverse=True, key=selector)
    result = list()
    rank_count = 0
    prev = None
    for item in lst:
        selected_item = item if selector is None else selector(item)
        if selected_item != prev:
            prev = selected_item
            rank_count += 1  
        if rank_count > top_n:
            break
        result.append(item)
        
    return result

global __search_recursion_counter

def search(lay :BaseLayout, top_n :int = 1, n_total_buildings :int = 38) -> list[SolutionItem]:
    """
    Searches the given layout for the optimal placement of accus

    Parameters:
    - lay               : A game layout which should only contain tiberium/crystal fields 
                          and no buildings
    - n_total_buildings : number of accus + power plants to place overall
    
    Returns:
    
    A list of SolutionItems representing the optimal solutions. I.e. all solutions returned will
    have an identical power rate, but different paths (which could be identical placements in 
    different order)
    """
    global __search_recursion_counter
    __search_recursion_counter = 0

    solutions :list[SolutionItem] = list()
    __search_recursive(lay, solutions, top_n, n_total_buildings)
    print(f"Recursion counter: {__search_recursion_counter}")
    return solutions

def __search_recursive(lay :BaseLayout, solutions :list[SolutionItem], top_n :int = 1, n_total_buildings :int = 38, path :list[PathNode] = list()):
    """
    Recursive part of the search() function, do not call directly
    """
    global __search_recursion_counter
    __search_recursion_counter += 1

    # get all fields where we can put an accu    
    empty_fields = lay.get_empty_fields()
    
    # set next accu on every possible field and compute the resulting power rate
    # these results are stored in an ordered list [([coord], rate)]
    coord_rate_map :list[PathNode] = list()
    for field in empty_fields:        
        lay.set(Constants.ACCU, field)
        rate = lay.get_total_power_rate(n_total_buildings - 1 - len(path))
        coord_rate_map.append(PathNode(coord=field, power_rate=rate))
        lay.set(Constants.EMPTY, field)
    
    # order by power rate descending, take top top_n entries (where equal rates count as one)
    next_coords :list[PathNode] = get_top_n_ranks(coord_rate_map, top_n, selector=lambda x: x.power_rate)
    for item in next_coords:
        # set accu and append coord to path
        lay.set(Constants.ACCU, item.coord)
        path.append(item)

        # add to solution if it's better than what we have
        if not solutions or item.power_rate >= solutions[0].power_rate:
            if not solutions or item.power_rate > solutions[0].power_rate:
                solutions.clear()                
            solutions.append(SolutionItem(power_rate=item.power_rate, path=path.copy()))

        # start recursion, only if solution is getting better
        if len(path) == 1 or path[-1].power_rate > path[-2].power_rate:
            __search_recursive(lay, solutions, top_n, n_total_buildings, path)

        lay.set(Constants.EMPTY, item.coord)
        path.pop()
