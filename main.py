from game_mechanics import *
from cnctaopt import CncTaOptParser
from searching import search
import time
from image2base import *
from pathlib import Path
import numpy as np

def sample_with_cnctaopt(cnctaopt_url :str, n_total_buildings :int=38, top_n :int=1):
    cnctaopt = CncTaOptParser(cnctaopt_url)
    lay = BaseLayout(cnctaopt.field)

    print(f"Analyzing layout {cnctaopt_url}, placing {n_total_buildings} buildings and using top_n={top_n}")

    # find solution
    start_time = time.time()
    solutions = search(lay, top_n=top_n, n_total_buildings=n_total_buildings)
    solution = solutions[0] # solutions are identical in terms of power rate, pick first

    # print stats
    print(f"Found {len(solutions)} solution(s) in {time.time()-start_time:.2f} sec")
    prev_rate = lay.get_total_power_rate(n_total_buildings)
    print(f"Max power production rate without accus: {prev_rate:,}/h")
    print(f"Best solution has {len(solution.path)} accus and a power rate of {solution.power_rate:,}/h")
    for node in solution.path:
        print(f"  ({node.coord[0]},{node.coord[1]}) - {node.power_rate:,}/h (+{node.power_rate-prev_rate:>12,}/h)")
        prev_rate = node.power_rate

    # generate solution layout and show url
    lay.set(Constants.ACCU, np.array([node.coord for node in solution.path], dtype=np.int32))
    lay.set_optimal_powerplants(n_total_buildings - len(solution.path))
    cnctaopt.assign(lay.field)
    print("CncTAOpt-Url to best layout:")
    print(cnctaopt.generate_url())

def sample_with_base_scanner_image(img_in :str, n_total_buildings :int=38, top_n :int=1):
    ib = Image2Base("images/anchor.png")

    start_time = time.time()    
    results = list()
    layouts = ib.find_layouts(img_in)
    best_solution = None
    best_layout = None
    for idx, layout in enumerate(layouts):
        pf = BaseLayout(layout[0])        
        solution = search(pf, top_n=top_n, n_total_buildings=n_total_buildings)[0]
        rate = solution.power_rate 
        print(f"Layout {idx:>2}: {rate:,}/h / {len(solution.path)} accus")

        center_coord = layout[1]
        results.append( (center_coord, rate) )

        if best_solution is None or best_solution.power_rate < rate:
            best_solution = solution
            best_layout = layout[0]

    # show stats
    runtime = time.time()-start_time
    print(f"Processed {len(layouts)} layouts in {runtime:.1f} seconds ({runtime/len(layouts):.3f} sec/layout)")
    print(f"Best layout found has power production rate of {best_solution.power_rate:,}/h")

    # write output image
    p = Path(img_in)
    img_out = f"{Path.joinpath(p.parent, p.stem + '_out' + p.suffix)}"
    ib.write_rates_to_image(img_in, img_out, results)
    print(f"Results written to {img_out}")

    # generate CncTAOpt-link to best layout
    pf = BaseLayout(best_layout)
    pf.set_accus([node.coord for node in best_solution.path])
    pf.set_optimal_powerplants(n_total_buildings - len(best_solution.path))
    cnctaopt = CncTaOptParser()
    cnctaopt.assign(pf)
    print("CncTAOpt-Url to best layout:")
    print(cnctaopt.generate_url())


sample_with_base_scanner_image("images/layouts_van16.png", n_total_buildings=38, top_n=1)

# best layout so far (14.12G/h)
#sample_with_cnctaopt("https://cnctaopt.com/FDjPl", n_total_buildings=38, top_n=1)

# example where top_n=1 and top_n=2 are very different:
#sample_with_cnctaopt("https://cnctaopt.com/UsO7C", n_total_buildings=38, top_n=1)
#sample_with_cnctaopt("https://cnctaopt.com/UsO7C", n_total_buildings=38, top_n=2)
