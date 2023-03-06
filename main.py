from app import best_power_layout_from_url, best_power_layout_from_image
from image2base import Image2Base
from pathlib import Path

if __name__ == "__main__":
    
    # looking for another 14.07 G/h layout:
    nbuildings=38
    topn=2
    threshold=13800000000
    for base in ['Minas_Tirith', 'Rivendell', 'Lothlorien', 'Mordor',  'Moria', 'Isengard', 'Shire',
                'Hobbiton', 'Rohan', 'Gondor', 'Bree', 'Rhun', 'Eriador', 'Ered_Luin', 'Fangorn', 
                'Middle_Earth', 'Angmar', 'Cardolan', 'Mirkwood', 'Enedwaith', 'Harlindon' ]:
        best_power_layout_from_image(f'images/{base}.png', nbuildings, topn, threshold)

    # run a search on a screenshot from the BaseScanner:
    #best_power_layout_from_image('sample_layouts.png', n_total_buildings=38, top_n=2, next_level_threshold=13800000000)

    # optimize some layouts given by a cnctaopt-link:
    #best_power_layout_from_url("https://cnctaopt.com/FDjPl", n_total_buildings=38, top_n=1) # 0.09s, 14.117 G/h