from game_mechanics import *
from cnctaopt import CncTaOptParser
from searching import search
import time

p = CncTaOptParser('https://cnctaopt.com/FDjPl')
pf = PowerField()
pf.set_resources(p.crystal_coords, p.tiberium_coords)
pf.set_accus(p.accu_coords)

start_time = time.time()
solutions = search(pf, top_n=1, n_total_buildings = 38)

print(f"Found {len(solutions)} solution(s) in {time.time()-start_time:.2f} sec")
print(f"Max power production rate without accus: {pf.get_total_rate(38):,}/h")
print(solutions[0])
pf.set_accus([node.coord for node in solutions[0].path])
pf.set_optimal_powerplants(38 - len(solutions[0].path))
p.assign(pf)
print(p.generate_url())
