import numpy as np
import time
import multiprocessing

from searching import DfsSearch, SearchResult, SolutionItem
from game import BaseLayout, Constants
from cnctaopt import CncTaOptParser
from image2base import Image2Base, ImageLayout, CoordinateRateTuple
from pathlib import Path

def best_power_layout_from_url(cnctaopt_url :str, n_total_buildings :int=38, top_n :int=1):
    """
    Parses a layout from the given CNCTAOpt url, then searches for the best possible power layout 
    using the given parameters.

    Parameters:
        - cnctaopt_url:      url to a layout on wwww.cnctaop.com. This can be a short url
                             the layout can be any faction an can contain any buildings.
                             These will all be ignored, only tiberium and crystal fields are considered
        - n_total_buildings: how many powerplants+accus to place in total
        - top_n :            number of top ranks to consider in the tree search. With top_n=1, 
                             always only the best position with the highest rate increase is chosen
                             (i.e. all of these if multiple with the same rate exist)
    """
    print(f"Analyzing layout {cnctaopt_url}, placing {n_total_buildings} buildings and using top_n={top_n}")

    cnctaopt = CncTaOptParser(cnctaopt_url)
    lay = BaseLayout(copy_from_array=cnctaopt.field, filter_field_type=Constants.TIBERIUM | Constants.CRYSTAL)

    # find solution
    search = DfsSearch(lay)
    result :SearchResult = search.find_best_power(top_n=top_n, n_total_buildings=n_total_buildings)
   
    # print stats
    print(result)
    prev_rate = lay.get_total_power_rate(n_total_buildings)
    print(f"Max power production rate without accus: {prev_rate:,}/h")
    print(f"Best solution has {result.best.num_accus} accus and a power rate of {result.best.power_rate:,}/h")
    for node in result.best.path:
        print(f"  ({node.coord[0]},{node.coord[1]}) - {node.power_rate:,}/h (+{node.power_rate-prev_rate:>13,}/h)")
        prev_rate = node.power_rate

    # generate solution layout and show url
    lay.set(Constants.ACCU, np.array([node.coord for node in result.best.path], dtype=np.int32))
    lay.set_optimal_powerplants(n_total_buildings - result.best.num_accus)
    cnctaopt.assign(lay.field)
    print(f"CncTAOpt-Url to best layout:\n{cnctaopt.generate_url()}\n\n")

class LayoutSearchResult:
    def __init__(self, layout_index :int, layout: ImageLayout, search_result :SearchResult):
        self.layout_index = layout_index
        self.layout = layout
        self.search_result = search_result

def best_power_layout_from_image(img_in :str, n_total_buildings :int=38, top_n :int=1, next_level_threshold :int=0):
    """
    Parses the given image which is the output of the BaseScanner script in TA.
    It tries to identify all layouts in this image finds the best power layout for each

    Args:
        img_in:            filename of an image (screenshot) with layouts
        n_total_buildings: total number of accus + powerplants to place
        top_n:             number of top ranks to consider in the tree search. With top_n=1, 
                           always only the best position with the highest rate increase is chosen
                           (i.e. all of these if multiple with the same rate exist)
        next_level_threshold:  if this is set to a value >0, the search is started with top_n=1 and then increased
                           to top_n if the power rate was bigger than this threshold
    """
    start_time = time.time()    

    # scan the given image    
    ib = Image2Base()
    layouts = ib.find_layouts(img_in)
    print(f"Reading layouts from {img_in}.. found {len(layouts)} layouts")

    # if we have a next_level_threshold, start always with top_n=1    
    if next_level_threshold > 0:
        top_n_start :int = 1
        top_n_next :int = top_n
        print(f"Searching for best layout starting with top_n={top_n_start}, increasing to {top_n_next} if result is >= {next_level_threshold/1000000000.0:.2f}G/h")
    else:
        top_n_start :int = top_n
        top_n_next :int = top_n
        print(f"Searching for best layout with top_n={top_n}")
    
    print_result = lambda idx, result: print(f"  Layout {idx:>2}: {result.best.power_rate:,}/h {result.best.num_accus:>2} accus {result.iterations:>5,} iterations {result.runtime:>8.3f} sec")
    print_stats = lambda n_layouts, runtime: print(f"Processed {n_layouts} layouts in {runtime:.1f} seconds ({runtime/n_layouts:.3f} sec/layout)")

    # we store all search reasults in a list of tuples : (layout-index, layout, search result)
    results :list[LayoutSearchResult] = []

    # first pass of search with top_n=top_n_start    
    for idx, layout in enumerate(layouts):
        result :SearchResult = _process_layout(layout, top_n_start, n_total_buildings)
        print_result(idx, result)
        results.append(LayoutSearchResult(idx, layout, result))
    n_first_pass_results = len(results)
    print_stats(n_first_pass_results, time.time()-start_time)

    # search again with a larger top_n, if requested
    start_time = time.time()
    if top_n_next > top_n_start:
        print(f"Repeat search with top_n={top_n_next}")
        for result_idx in range(n_first_pass_results):
            if results[result_idx].search_result.best.power_rate > next_level_threshold:                
                result :SearchResult = _process_layout(layout, top_n_next, n_total_buildings)
                results.append(LayoutSearchResult(idx, layout, result))
                print_result(idx, result)
        print_stats(len(results)-n_first_pass_results, time.time()-start_time)
    
    # show stats
    results.sort(reverse=True, key=lambda x: x.search_result.best.power_rate)
    print(f"Best layout is {results[0].layout_index} and has a power production rate of { results[0].search_result.best.power_rate:,}/h")

    # write output image
    p = Path(img_in)
    pars = f"_b{n_total_buildings}_topn{top_n}"
    img_out = f"{Path.joinpath(p.parent, p.stem + pars + p.suffix)}"
    ib.write_rates_to_image(img_in, img_out, [CoordinateRateTuple(r.layout_index, r.layout.coord, r.search_result.best.power_rate) for r in results])
    print(f"Results written to {img_out}")

    # generate CncTAOpt-link to best layout
    lay = BaseLayout(copy_from_array=results[0].layout.data)
    lay.set(Constants.ACCU, np.array([node.coord for node in results[0].search_result.best.path], dtype=np.int32))
    lay.set_optimal_powerplants(n_total_buildings - len(results[0].search_result.best.path))
    cnctaopt = CncTaOptParser(field = lay.field)
    print(f"CncTAOpt-Url to best layout:\n{cnctaopt.generate_url()}\n\n")

def _process_layout(layout: ImageLayout, top_n :int, n_total_buildings :int) -> SearchResult:
    search = DfsSearch(BaseLayout(layout.data))        
    result :SearchResult = search.find_best_power(top_n=top_n, n_total_buildings=n_total_buildings)
    return result
    
