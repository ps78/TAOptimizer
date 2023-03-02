import numpy as np
import time

from searching import DfsSearch, SearchResult, SolutionItem
from game import BaseLayout, Constants
from cnctaopt import CncTaOptParser
from image2base import Image2Base, ImageLayout
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
    cnctaopt = CncTaOptParser(cnctaopt_url)
    lay = BaseLayout(cnctaopt.field, Constants.TIBERIUM | Constants.CRYSTAL)

    print(f"Analyzing layout {cnctaopt_url}, placing {n_total_buildings} buildings and using top_n={top_n}")

    # find solution
    search = DfsSearch(lay)
    result :SearchResult = search.find_best_power(top_n=top_n, n_total_buildings=n_total_buildings)
    solution :SolutionItem = result.solutions[0] # solutions are identical in terms of power rate, pick first

    # print stats
    print(result)
    prev_rate = lay.get_total_power_rate(n_total_buildings)
    print(f"Max power production rate without accus: {prev_rate:,}/h")
    print(f"Best solution has {len(solution.path)} accus and a power rate of {solution.power_rate:,}/h")
    for node in solution.path:
        print(f"  ({node.coord[0]},{node.coord[1]}) - {node.power_rate:,}/h (+{node.power_rate-prev_rate:>13,}/h)")
        prev_rate = node.power_rate

    # generate solution layout and show url
    lay.set(Constants.ACCU, np.array([node.coord for node in solution.path], dtype=np.int32))
    lay.set_optimal_powerplants(n_total_buildings - len(solution.path))
    cnctaopt.assign(lay.field)
    print(f"CncTAOpt-Url to best layout:\n{cnctaopt.generate_url()}\n\n")

def best_power_layout_from_image(img_in :str, n_total_buildings :int=38, top_n :int=1):
    """
    Parses the given image which is the output of the BaseScanner script in TA.
    It tries to identify all layouts in this image finds the best power layout for each

    Args:
        img_in:            filename of an image (screenshot) with layouts
        n_total_buildings: total number of accus + powerplants to place
        top_n:             number of top ranks to consider in the tree search. With top_n=1, 
                           always only the best position with the highest rate increase is chosen
                           (i.e. all of these if multiple with the same rate exist)
    """
    ib = Image2Base()

    # scan the given image
    start_time = time.time()
    results = list()
    print(f"Reading layouts from {img_in}")
    layouts = ib.find_layouts(img_in)
    best_result :SearchResult = None
    best_layout :ImageLayout = None
    for idx, layout in enumerate(layouts):
        search = DfsSearch(BaseLayout(layout.data))
        result :SearchResult = search.find_best_power(top_n=top_n, n_total_buildings=n_total_buildings)
        solution = result.solutions[0]
        print(f"  Layout {idx:>2}: {solution.power_rate:,}/h / {len(solution.path)} accus")

        center_coord = layout.coord
        results.append( (center_coord, solution.power_rate) )

        if best_result is None or best_result.solutions[0].power_rate < solution.power_rate:
            best_result = result
            best_layout = layout

    # show stats
    runtime = time.time()-start_time
    print(f"Processed {len(layouts)} layouts in {runtime:.1f} seconds ({runtime/len(layouts):.3f} sec/layout)")
    print(f"Best layout found has power production rate of {best_result.solutions[0].power_rate:,}/h")

    # write output image
    p = Path(img_in)
    img_out = f"{Path.joinpath(p.parent, p.stem + '_out' + p.suffix)}"
    ib.write_rates_to_image(img_in, img_out, results)
    print(f"Results written to {img_out}")

    # generate CncTAOpt-link to best layout
    lay = BaseLayout(copy_from_array=best_layout.data)
    lay.set(Constants.ACCU, np.array([node.coord for node in best_result.solutions[0].path], dtype=np.int32))
    lay.set_optimal_powerplants(n_total_buildings - len(best_result.solutions[0].path))
    cnctaopt = CncTaOptParser(field = lay.field)
    print(f"CncTAOpt-Url to best layout:\n{cnctaopt.generate_url()}\n\n")