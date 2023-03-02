from app import best_power_layout_from_url, best_power_layout_from_image

# run a search on a screenshot from the BaseScanner:
best_power_layout_from_image('sample_layouts.png', n_total_buildings=38, top_n=1)

# optimize some layouts given by a cnctaopt-link:
best_power_layout_from_url("https://cnctaopt.com/FDjPl", n_total_buildings=38, top_n=1) # 0.09s, 14.117 G/h

# example where top_n=1 and top_n=2 return quite different results:
best_power_layout_from_url("https://cnctaopt.com/UsO7C", n_total_buildings=38, top_n=1) # 0.15s
best_power_layout_from_url("https://cnctaopt.com/UsO7C", n_total_buildings=38, top_n=2) # 33s

best_power_layout_from_url("https://cnctaopt.com/XD7Uk", n_total_buildings=38, top_n=1) # 0.63s, 13.956 G/h
best_power_layout_from_url("https://cnctaopt.com/XD7Uk", n_total_buildings=38, top_n=2) # 35s, 14.020 G/h , [696:673]
