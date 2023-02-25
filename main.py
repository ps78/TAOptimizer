from game_mechanics import *
from cnctaopt import CncTaOptParser
from searching import search
import time
from image2base import *

def sample_with_cnctaopt():
    #p = CncTaOptParser('https://cnctaopt.com/FDjPl') 14.12G layout
    p = CncTaOptParser("https://cnctaopt.com/CbUEY")
    pf = PowerField()
    pf.set_resources(p.crystal_coords, p.tiberium_coords)
    start_time = time.time()
    solutions = search(pf, top_n=1, n_total_buildings = 38)
    print(f"Found {len(solutions)} solution(s) in {time.time()-start_time:.2f} sec")
    print(f"Max power production rate without accus: {pf.get_total_rate(38):,}/h")
    print(solutions[0])
    pf.set_accus([node.coord for node in solutions[0].path])
    pf.set_optimal_powerplants(38 - len(solutions[0].path))
    p.assign(pf)
    print(p.generate_url())

def sample_with_base_scanner_image(img_in, img_out):
    ib = Image2Base("anchor.png")
    
    results = list()
    for idx, layout in enumerate(ib.find_layouts(img_in)):
        pf = PowerField(layout[0])        
        solution = search(pf, top_n=1, n_total_buildings=38)[0]
        rate = solution.power_rate 
        print(f"Layout {idx}: {rate:,}/h")

        center_coord = layout[1]
        results.append( (center_coord, rate) )
    
    ib.write_rates_to_image(img_in, img_out, results)

sample_with_base_scanner_image("layouts.png", "output.png")