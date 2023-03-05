from app import best_power_layout_from_url, best_power_layout_from_image
from image2base import Image2Base

#best_power_layout_from_url("https://cnctaopt.com/EPWsn", n_total_buildings=38, top_n=2) # 14.03
#best_power_layout_from_url("https://cnctaopt.com/3yrxR", n_total_buildings=38, top_n=2) # 14.07

# looking for another 14.07 G/h layout:
#best_power_layout_from_image('images/van16.png', n_total_buildings=38, top_n=1)
#best_power_layout_from_image('images/van15.png', n_total_buildings=38, top_n=1)
#best_power_layout_from_image('images/van14.png', n_total_buildings=38, top_n=1)
#best_power_layout_from_image('images/van13.png', n_total_buildings=38, top_n=1)
#best_power_layout_from_image('images/van12.png', n_total_buildings=38, top_n=1)
#best_power_layout_from_image('images/van11.png', n_total_buildings=38, top_n=1)
#best_power_layout_from_image('images/van10.png', n_total_buildings=38, top_n=1)

# run a search on a screenshot from the BaseScanner:
best_power_layout_from_image('sample_layouts.png', n_total_buildings=38, top_n=2, next_level_threshold=13600000000)

# optimize some layouts given by a cnctaopt-link:
#best_power_layout_from_url("https://cnctaopt.com/FDjPl", n_total_buildings=38, top_n=1) # 0.09s, 14.117 G/h

# example where top_n=1 and top_n=2 return quite different results:
#best_power_layout_from_url("https://cnctaopt.com/UsO7C", n_total_buildings=38, top_n=1) # 0.15s
#best_power_layout_from_url("https://cnctaopt.com/UsO7C", n_total_buildings=38, top_n=2) # 33s

#best_power_layout_from_url("https://cnctaopt.com/XD7Uk", n_total_buildings=38, top_n=1) # 0.63s, 13.956 G/h
#best_power_layout_from_url("https://cnctaopt.com/XD7Uk", n_total_buildings=38, top_n=2) # 35s, 14.020 G/h , [696:673]
