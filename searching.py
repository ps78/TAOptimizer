from game import BaseLayout
import time

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
    @property
    def num_accus(self) -> int:
        """
        Returns the number of accus in the solution, i.e. the path length
        """
        return len(self.path)
 
    def __init__(self, power_rate :int, path :list[PathNode]):
        self.power_rate = power_rate
        self.path = path

    def __str__(self):
        s = f"Solution with {len(self.path)} accus, power rate: {self.power_rate:,})\n"
        for node in self.path:
            s += f"   {node}\n"
        return s

class SearchResult:
    """
    The result of a search. Can contain multiple solutions
    """
    @property
    def solutions(self) -> list[SolutionItem]:
        """
        list of solution items
        """
        return self.__solutions

    @property 
    def best(self) -> SolutionItem|None:
        """
        Reference to the best solution
        """
        return None if not any(self.__solutions) else self.__solutions[0]

    @property
    def runtime(self) -> float:
        """
        Total runtime in seconds
        this is automatically calculated as time difference between
        the last solution added and the constructor call        
        """
        return self.__runtime

    @property
    def num_solutions(self) -> int:
        """
        Number of solutions
        """
        return len(self.__solutions)

    @property
    def iterations(self) -> int:
        """
        Number of iterations used to find the solution (calls of the recursive search function)
        """
        return self.__iterations

    def __init__(self):
        self.__solutions :list[SolutionItem] = []
        self.__runtime :int = 0
        self.__iterations :int = 0
        self.__start = time.time()

    def add_solution(self, sol :SolutionItem):
        """
        Adds an additional solution and updates the runtime
        """
        self.__solutions.append(sol)
        self.__runtime = time.time()-self.__start

    def clear_solutions(self):
        """
        Remove all solutions
        """
        self.__solutions.clear()

    def inc_iterations(self):
        """
        Increment the iteration counter by one
        """
        self.__iterations += 1

    def __str__(self) -> str:
        s = f"Found {self.num_solutions} solution(s) in {self.runtime:.3f} sec ({self.iterations:,} iterations)"
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

class DfsSearch():
    """
    A depth-first tree search implementation
    """
    def __init__(self, layout :BaseLayout):
        self.__layout :BaseLayout = layout.copy()
        self.__recursion = 0

    def find_best_power(self, top_n :int = 1, n_total_buildings :int = 38) -> SearchResult:
        search_result = SearchResult()        
        self.__find_best_power_recursive(search_result, top_n, n_total_buildings)        
        return search_result

    def __find_best_power_recursive(self, search_result :SearchResult, top_n :int = 1, n_total_buildings :int = 38, path :list[PathNode] = list()):
        """
        Recursive part of the search() function, do not call directly
        """
        search_result.inc_iterations()

        # get all fields where we can put an accu    
        empty_fields = self.__layout.get_empty_fields()
        
        # set next accu on every possible field and compute the resulting power rate
        # these results are stored in an ordered list [([coord], rate)]
        coord_rate_map :list[PathNode] = list()
        for field in empty_fields:        
            #self.__layout.set(Constants.ACCU, field)
            self.__layout.set_accu(field)
            rate = self.__layout.get_total_power_rate(n_total_buildings - 1 - len(path))
            coord_rate_map.append(PathNode(coord=field, power_rate=rate))
            #self.__layout.set(Constants.EMPTY, field)
            self.__layout.remove_accu(field)
        
        # order by power rate descending, take top top_n entries (where equal rates count as one)
        next_coords :list[PathNode] = get_top_n_ranks(coord_rate_map, top_n, selector=lambda x: x.power_rate)
        for item in next_coords:
            # set accu and append coord to path
            #self.__layout.set(Constants.ACCU, item.coord)
            self.__layout.set_accu(item.coord)
            path.append(item)

            # if we found a solution that's better than what we have, clear all solutions and add it
            # if it's identical, just add it
            if search_result.num_solutions==0 or item.power_rate >= search_result.solutions[0].power_rate:
                if search_result.num_solutions>0 and item.power_rate > search_result.solutions[0].power_rate:
                    search_result.clear_solutions()
                search_result.add_solution(SolutionItem(power_rate=item.power_rate, path=path.copy()))

            # start recursion, only if solution is getting better
            if len(path) == 1 or path[-1].power_rate > path[-2].power_rate:
                self.__find_best_power_recursive(search_result, top_n, n_total_buildings, path)

            #self.__layout.set(Constants.EMPTY, item.coord)
            self.__layout.remove_accu(item.coord)
            path.pop()
