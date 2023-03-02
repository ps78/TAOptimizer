from app import best_power_layout_from_url, best_power_layout_from_image

best_power_layout_from_image('images/layouts_small.png', n_total_buildings=38, top_n=1)

best_power_layout_from_url("https://cnctaopt.com/FDjPl", n_total_buildings=38, top_n=1) # 0.09s, 14.117 G/h
best_power_layout_from_url("https://cnctaopt.com/XD7Uk", n_total_buildings=38, top_n=1) # 0.63s, 13.956 G/h
#best_power_layout_from_url("https://cnctaopt.com/XD7Uk", n_total_buildings=38, top_n=2) # 35s, 14.020 G/h , [696:673]

# example where top_n=1 and top_n=2 are very different:
best_power_layout_from_url("https://cnctaopt.com/UsO7C", n_total_buildings=38, top_n=1) # 6.3s
#best_power_layout_from_url("https://cnctaopt.com/UsO7C", n_total_buildings=38, top_n=2) # 31s
