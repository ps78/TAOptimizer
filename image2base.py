import cv2
import numpy as np
from game_mechanics import Constants

class Image2Base:
    """
    Imgage2Base can extract the base layouts from an 
    image (screenshot) of the base-scanner output
    """
    
    def __init__(self, anchor_img :str = "anchor.png", layout_offset :tuple = (1, 20), layout_dim :tuple = (144, 158)):
        """
        Constructor

        Parameters
            - anchor_img: image file containing the anchor image used to detect the individual base layouts 
                          within the screenshot 
            - layout_offset: (x,y) coordinate offset from the anchor image to the top-left corner of the layout
            - layout_dim : (width, height) in pixels of a single base layout
        """
        self.__anchor_img = anchor_img
        self.__layout_offset = layout_offset
        self.__layout_dim = layout_dim

    def find_layouts(self, layouts_img :str) -> list[(np.ndarray, tuple)]:
        """
        Detects and extracts all base layouts in the image

        Parameters:
            - layout_img: screenshot from the base scanner output

        Returns:
            - List of tuples (base-array (2D np-arrays), center coordinate)
        """
        img_rgb = cv2.imread(layouts_img)
        template = cv2.imread(self.__anchor_img)
        w, h = template.shape[:-1]
        res = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
        threshold = .9
        loc = np.where(res >= threshold)

        cell_dim = (self.__layout_dim[0] / float(Constants.BASE_COLUMNS), self.__layout_dim[1] / float(Constants.BASE_ROWS))        
        layouts = list()

        for pt in zip(*loc[::-1]):  # Switch columns and rows
            topleft = (pt[0] + self.__layout_offset[0], pt[1] + self.__layout_offset[1])
            base_center = (topleft[0] + self.__layout_dim[0]//2, topleft[1] + self.__layout_dim[1]//2)
            base_arr = np.zeros((Constants.BASE_ROWS, Constants.BASE_COLUMNS), dtype=np.int32)
            for row in range(Constants.BASE_ROWS):
                for col in range(Constants.BASE_COLUMNS):
                    cell_center = (topleft[0] + int((col+0.5)*cell_dim[0]), int(topleft[1] + (row+0.5)*cell_dim[1]))
                    base_arr[row, col] = self._detect_cell_type(img_rgb, cell_center)
                    # for debugging:
                    #cv2.circle(img_rgb, center=cell_center, radius=3, thickness=1, color=(0,0,255)) 

            layouts.append((base_arr, base_center))

        # for debugging:
        #cv2.imwrite('result.png', img_rgb)
        return layouts

    def _detect_cell_type(self, img, coord :tuple) -> int:
        """
        Detects the cell type from the image at the given coordinate.
        Averages the colors over a small region around the coordinate

        Parameters:
            - img: color image
            - coord: coordiate (tuple) where to look

        Returns:
            - Constants.EMPTY|TIBERIUM|CRYSTAL
        """
        delta = 3
        
        # we average over the region coord+/-delta
        (b,g,r) = np.mean(img[coord[1]-delta:coord[1]+delta, coord[0]-delta:coord[0]+delta, :], axis=(0,1))

        # these are the results for delta=3:
        # tiberium : (42,158,40)  //  (97, 163 , 58)
        # crystal:   (198,177,43) // (158, 118, 41)
        # background: (48,48,48)

        if b > 120 and g < 140:
            return Constants.CRYSTAL
        elif b < 120 and g > 140:
            return Constants.TIBERIUM
        else:
            return Constants.EMPTY

    def write_rates_to_image(self, input_image :str, output_image :str, data :list[tuple]):
        img = cv2.imread(input_image)
        max_rate = max([item[1] for item in data])
        for item in data:
            coord = (int(item[0][0]-self.__layout_dim[0]/2), item[0][1])
            rate = f"{item[1]/1000000000.0:.3f}G/h"            
            
            if item[1] == max_rate:
                outer_color = (0,255,255)
                inner_color = (0,0,255)
            else:
                outer_color = (255,255,255)
                inner_color = (0,0,0)
            
            cv2.putText(img, text=rate, org=coord, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8, color=outer_color, thickness=3, lineType=cv2.LINE_AA)
            cv2.putText(img, text=rate, org=coord, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8, color=inner_color, thickness=1, lineType=cv2.LINE_AA)

        cv2.imwrite(output_image, img)
        print(f"Best layout found has {max_rate:,} G/h. Results written to {output_image}")