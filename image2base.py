import cv2
import numpy as np
from game import Constants

class ImageLayout:
    """
    Represents a base layout in an image
    """
    @property 
    def data(self) -> np.ndarray:
        return self.__data

    @property
    def coord(self) -> tuple[int,int]:
        return self.__coord

    def __init__(self, data :np.ndarray, coord :tuple[int,int]):
        self.__data = data
        self.__coord = coord

class CoordinateRateTuple:
    def __init__(self, layout_index:int, coord :tuple[int,int], rate :int):
        self.layout_index = layout_index
        self.coord = coord
        self.rate = rate

class Image2Base:
    """
    Imgage2Base can extract the base layouts from an 
    image (screenshot) of the base-scanner output
    """
    DEFAULT_ANCHOR_IMG :str = "anchor.png"
    DEFAULT_LAYOUT_OFFSET :tuple[int,int] = (1,20)
    DEFAULT_LAYOUT_DIM :tuple[int,int] = (144, 158)

    def __init__(self, 
                    anchor_img :str = DEFAULT_ANCHOR_IMG, 
                    layout_offset :tuple[int,int] = DEFAULT_LAYOUT_OFFSET, 
                    layout_dim :tuple[int,int] = DEFAULT_LAYOUT_DIM):
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

    def find_layouts(self, layouts_img :str) -> list[ImageLayout]:
        """
        Detects and extracts all base layouts in the image

        Parameters:
            - layout_img: screenshot from the base scanner output

        Returns:
            - List of tuples (base-array (2D np-arrays), center coordinate)
        """
        # import the image and the template
        img_rgb = cv2.imread(layouts_img)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template = cv2.imread(self.__anchor_img)

        # find all instances of the template within the image
        res = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
        threshold = .9
        loc = np.where(res >= threshold)

        # deduct the size in pixels of one cell(field) within a lyayout
        cell_dim = (self.__layout_dim[0] / float(Constants.BASE_COLUMNS), self.__layout_dim[1] / float(Constants.BASE_ROWS))        
        layouts = list()
        
        # iterate through all layouts found in the image
        for pt in zip(*loc[::-1]):  # Switch columns and rows
            # top-left coordinate in pixels of the current layout within the image
            topleft = (pt[0] + self.__layout_offset[0], pt[1] + self.__layout_offset[1])
            # center coordinate of the layout, used to place text later
            base_center = (topleft[0] + self.__layout_dim[0]//2, topleft[1] + self.__layout_dim[1]//2)
            
            # check each cell of the layout and decide if it's empty, contains tiberium or crystal
            base_arr = np.zeros((Constants.BASE_ROWS, Constants.BASE_COLUMNS), dtype=np.int32)
            for row in range(Constants.BASE_ROWS):
                for col in range(Constants.BASE_COLUMNS):
                    # we look at the average color of the pixels in the center of the cell:
                    cell_center = (topleft[0] + int((col+0.5)*cell_dim[0]), int(topleft[1] + (row+0.5)*cell_dim[1]))
                    base_arr[row, col] = self._detect_cell_type(img_rgb, cell_center)
                    # for debugging:
                    #cv2.circle(img_rgb, center=cell_center, radius=3, thickness=1, color=(0,0,255)) 
                    
            # check that we have a valid layout with 12 resource field, ignore it if not (the image might have been cropped)
            if np.sum(base_arr == Constants.TIBERIUM) + np.sum(base_arr == Constants.CRYSTAL) == 12:
                layouts.append(ImageLayout(base_arr, base_center))

        # for debugging:
        #cv2.imwrite('result.png', img_rgb)
        return layouts

    def _detect_cell_type(self, img, coord :tuple[int,int]) -> int:
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

    def write_rates_to_image(self, input_image :str, output_image :str, data :list[CoordinateRateTuple]):
        """
        Write the rates provided in data into the impage provided by input_image and
        stores the result in the output-image

        Parameters:
            - input_image: file name of the image to read
            - output_image: file name of the image file to create with the rates 
            - data: list containing one element for each layout in the input image
                    each element in the list is a tuple <coord, rate>
        """
        img = cv2.imread(input_image)
        max_rate = max([item.rate for item in data])
        
        for layout_index in [item.layout_index for item in data]:
            # get the element if this layout index which has the highest rate
            item = sorted([item for item in data if item.layout_index == layout_index], reverse=True, key=lambda x:x.rate)[0]

            coord = (int(item.coord[0]-self.__layout_dim[0]/2), item.coord[1])
            rate = f"{item.rate/1000000000.0:.3f}G/h"            
            
            if item.rate == max_rate:
                outer_color = (0,255,255)
                inner_color = (0,0,255)
            else:
                outer_color = (255,255,255)
                inner_color = (0,0,0)
            
            cv2.putText(img, text=rate, org=coord, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8, color=outer_color, thickness=3, lineType=cv2.LINE_AA)
            cv2.putText(img, text=rate, org=coord, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8, color=inner_color, thickness=1, lineType=cv2.LINE_AA)

        cv2.imwrite(output_image, img)