from app import best_power_layout_from_url, best_power_layout_from_image
from image2base import Image2Base

if __name__ == "__main__":
    #best_power_layout_from_url("https://cnctaopt.com/EPWsn", n_total_buildings=38, top_n=2) # 14.03
    #best_power_layout_from_url("https://cnctaopt.com/3yrxR", n_total_buildings=38, top_n=2) # 14.07

    # looking for another 14.07 G/h layout:
    nbuildings=38
    topn=2
    threshold=13800000000
    best_power_layout_from_image('images/van16.png', nbuildings, topn, threshold)
    best_power_layout_from_image('images/van15.png', nbuildings, topn, threshold)
    best_power_layout_from_image('images/van14.png', nbuildings, topn, threshold)
    best_power_layout_from_image('images/van13.png', nbuildings, topn, threshold)
    best_power_layout_from_image('images/van12.png', nbuildings, topn, threshold)
    best_power_layout_from_image('images/van11.png', nbuildings, topn, threshold)
    best_power_layout_from_image('images/van10.png', nbuildings, topn, threshold)

    # run a search on a screenshot from the BaseScanner:
    #best_power_layout_from_image('sample_layouts.png', n_total_buildings=38, top_n=2, next_level_threshold=13800000000)

    # optimize some layouts given by a cnctaopt-link:
    #best_power_layout_from_url("https://cnctaopt.com/FDjPl", n_total_buildings=38, top_n=1) # 0.09s, 14.117 G/h

    # example where top_n=1 and top_n=2 return quite different results:
    #best_power_layout_from_url("https://cnctaopt.com/UsO7C", n_total_buildings=38, top_n=1) # 0.15s
    #best_power_layout_from_url("https://cnctaopt.com/UsO7C", n_total_buildings=38, top_n=2) # 33s

    #best_power_layout_from_url("https://cnctaopt.com/XD7Uk", n_total_buildings=38, top_n=1) # 0.63s, 13.956 G/h
    #best_power_layout_from_url("https://cnctaopt.com/XD7Uk", n_total_buildings=38, top_n=2) # 35s, 14.020 G/h , [696:673]
