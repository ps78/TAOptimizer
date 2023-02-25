import numpy as np
import numpy.typing as npt
from collections import namedtuple

class Constants:
    """
    Contains production rates of power plants and provides
    a method to return the accurate production rate of a power plant
    given a number of adjacient accus crystal fields
    """
    # power/h production rate of a power plant without any accu or crystal field
    BASE_POWER_RATE = 159653145

    # power/h induced in the power plant per adjacient crystal field
    CRYSTAL_POWER_RATE = 79370420

    # power/h induced in the power plant per adjacient accumulator
    ACCU_POWER_RATE = 63633182

    # power/h induced as bonus if at least one accu is adjacient to the power plant
    ACCU_POWER_BONUS = 95791887

    # dimension of a base
    BASE_ROWS = 8
    BASE_COLUMNS = 9
    BASE_OFFENSE_ROWS = 4

    # resource/building types
    EMPTY = 0
    CRYSTAL = 1
    TIBERIUM = 2
    ACCU = 4
    POWERPLANT = 8

    def get_power_rate(num_accus :int, num_crystal :int) -> int:
        """
        Returns the overall power production rate of a power plant with
        num_accus adjacient accumulators and num_crystal adjacient crystal
        fields
        """
        return Constants.BASE_POWER_RATE \
                + (Constants.ACCU_POWER_BONUS if num_accus > 0 else 0) \
                + num_accus * Constants.ACCU_POWER_RATE \
                + num_crystal * Constants.CRYSTAL_POWER_RATE

class PowerPlantFieldCategory:
    """
    This type is used by class Layout to store records representing
    a category of fields where power plants can be placed. The attributes are:
    - num_accus :int    Number of accumulators adjacient to the field
    - num_crystal :int  Number of crystal fields adjacient to the field
    - num_field :int    Total number of fields of this category in the layout
    - power_rate :int   Power production rate per hour of one field of this category
    """
    def __init__(self, rate :int, num_fields :int, coords :list[tuple]):
        self.rate = rate
        self.num_fields = num_fields
        self.coords = coords

    def __str__(self):
        return f"{self.rate:,}/h - {self.num_fields} fields"

def enumerate_adjacent_coords(arr :np.ndarray, coord :npt.ArrayLike) -> np.ndarray:
    """
    Enumerates the coordinates of the 3x3 field with coord in the center, 
    but does not return the center coordinate.
    If this 3x3 crosses the border of the given array, coordinates are skipped

    Parameters:
    - arr   : 2D numpy array
    - coord : tuple or list with two elements or numpy array with 2 elements defining the
              center coordinate

    Returns:
    - 2D numpy array of shape 3x3 in general potentially smaller depending on arr
    """
    row, col = coord[0], coord[1]
    start_row = 0 if row == 0 else row-1
    end_row =  arr.shape[0] if row == arr.shape[0]-1 else row+2
    start_col = 0 if col == 0 else col-1
    end_col =  arr.shape[1] if col == arr.shape[1]-1 else col+2
    coords = np.empty(((end_row-start_row)*(end_col-start_col)-1, 2), dtype=np.int32)
    idx = 0
    for r in range(start_row, end_row):
        for c in range(start_col, end_col):
            if not (r == row and c == col):
                coords[idx, 0] = r
                coords[idx, 1] = c
                idx += 1
    return coords

class PowerField:
    """
    Type to hold information about everything affecting the power
    production rate of a base. 
    All information is stored in 2D-numpy arrays to speed up calculations
    """
    @property
    def adjacent_crystal(self) -> np.ndarray:
        """
        2D numpy array with the number of crystal fields adjacent to every
        field
        """
        return self.__adjacent_crystal

    @property
    def adjacent_accu(self) -> np.ndarray:
        """
        2D numpy array with the number of accumulators adjacent to every
        field
        """
        return self.__adjacent_accu

    @property
    def resource(self) -> np.ndarray:
        """
        A field showing 0 at coordinates without resources
        and TIBERIUM or CRYSTAL if there are resources
        """
        return self.__resource

    @property
    def building(self) -> np.ndarray:
        """
        A field showing the building at each coordinate
        """
        return self.__building

    @property
    def rate(self) -> np.ndarray:
        """
        2D numpy array with total theoretical power production rate on every field
        in case a power plant is placed there
        """
        return self.__rate

    def __init__(self, arr :np.ndarray = None):
        self.__adjacent_crystal = self.__create_field(np.int32)
        self.__adjacent_accu = self.__create_field(np.int32)
        self.__resource = self.__create_field(np.int32) 
        self.__building = self.__create_field(np.int32)
        self.__rate = self.__create_field(np.int64) + Constants.BASE_POWER_RATE
        if arr is not None:
            self.assign(arr)

    def assign(self, arr :np.ndarray):
        """
        Loads the data from the given 2D-numpy array
        """
        crystal = []
        tiberium = []
        for row in range(Constants.BASE_ROWS):
            for col in range(Constants.BASE_COLUMNS):
                match arr[row,col]:
                    case Constants.TIBERIUM:
                        tiberium.append((row,col))
                    case Constants.CRYSTAL:
                        crystal.append((row, col))
                    case Constants.EMPTY:
                        pass
                    case _:
                        self.set_building((row, col), arr[row, col], suppress_refresh_rate=True)
        self.set_resources(crystal_coords=crystal, tiberium_coords=tiberium)

    def __create_field(self, dtype):
        """
        Creates a zero-ed 2D numpy array with the given dtype. Dimensions are
        taken from the Constants BASE_ROWS/COLUMNS
        """
        return np.zeros((Constants.BASE_ROWS, Constants.BASE_COLUMNS), dtype=dtype)

    def set_resources(self, crystal_coords :list, tiberium_coords :list):
        """
        Sets crystal/tiberium at the given coordinates.
        Updates __resource and __adjacent_crystal arrays
        """    
        if tiberium_coords is not None:
            for coord in tiberium_coords:
                self.__resource[coord[0], coord[1]] = Constants.TIBERIUM

        if crystal_coords is not None:
            for coord in crystal_coords:
                self.__resource[coord[0], coord[1]] = Constants.CRYSTAL
                for c in enumerate_adjacent_coords(self.__adjacent_crystal, coord):
                    self.__adjacent_crystal[c[0], c[1]] += 1
            self._refresh_rate()

    def set_building(self, coord :tuple, building_type :int, suppress_refresh_rate :bool = False):
        """
        Places accu(s) at the given coordinate(s)
        Updates fields __accu, __adjacent_accu and __rate

        Parameter:
        - coord: tuple (row, col) with the coordinate
        - present: True -> place accu, False-> remove accu
        """        
        row, col = coord[0], coord[1]
        clear_accu = self.__building[row, col] == Constants.ACCU
        self.__building[row, col] = building_type
        if building_type == Constants.ACCU or clear_accu:
            for c in enumerate_adjacent_coords(self.__adjacent_crystal, coord):
                self.__adjacent_accu[c[0], c[1]] += 1 if building_type==Constants.ACCU else -1

        if not suppress_refresh_rate:
            self._refresh_rate()

    def set_accus(self, coords :list, present :bool = True):
        if present:
            for coord in coords:
                self.set_building(coord, Constants.ACCU, suppress_refresh_rate=True)
        else:
            for coord in coords:
                self.set_building(coord, Constants.EMPTY, suppress_refresh_rate=True)

        self._refresh_rate()

    def set_optimal_powerplants(self, num_powerplants :int):
        categories = self.get_field_categories(num_powerplants)
        for cat in categories:
            for coord in cat.coords:
                self.__building[coord[0], coord[1]] = Constants.POWERPLANT

    def _refresh_rate(self):
        """
        Recalculates the __rate array
        """
        self.__rate = self.__adjacent_crystal * Constants.CRYSTAL_POWER_RATE + \
                        self.__adjacent_accu * Constants.ACCU_POWER_RATE + \
                        (self.__adjacent_accu >= 1) * Constants.ACCU_POWER_BONUS + \
                        Constants.BASE_POWER_RATE
    
    def get_field_categories(self, power_plant_limit :int = -1) -> list[PowerPlantFieldCategory]:
        """
        Returns a list with one entry per field category. All empty fields of the 
        base are categorized by the power production rate of a power plant that
        is placed there.
        The list is ordered with the highest production rate first

        Parameters:
            - power_plant_limit: maximum number of power plants to place. If -1: limited only 
                                 by the number of empty fields
        """
        categories :dict[int, PowerPlantFieldCategory] = dict()
        for row in range(Constants.BASE_ROWS):
            for col in range(Constants.BASE_COLUMNS):
                if self.__resource[row, col] == Constants.EMPTY and self.__building[row, col] == Constants.EMPTY:
                    rate = self.__rate[row, col]
                    if rate in categories.keys():
                        categories[rate].num_fields += 1
                        categories[rate].coords.append((row, col))
                    else:
                        categories[rate] = PowerPlantFieldCategory(rate, 1, [(row, col)])

        sorted_categories = sorted(categories.items(), key=lambda x: x[0], reverse=True)
        if power_plant_limit == -1:
            return [item[1] for item in sorted_categories.items()]
        else:
            result = list()
            pp_left = power_plant_limit
            for cat in sorted_categories:
                if pp_left > cat[1].num_fields:
                    pp_left -= cat[1].num_fields
                    result.append(cat[1])
                else:
                    result.append(PowerPlantFieldCategory(cat[1].rate, pp_left, cat[1].coords[:pp_left]))
                    break
            return result

    def get_total_rate(self, powerplants :int) -> int:
        return sum([int(cat.rate)*int(cat.num_fields) for cat in self.get_field_categories(powerplants)])

    def get_empty_fields(self):
        return np.argwhere(self.__resource + self.building == Constants.EMPTY)

    def __str__(self):
        s = ""
        for row in range(Constants.BASE_ROWS):
            for col in range(Constants.BASE_COLUMNS):
                ch = '.'
                match self.__resource[row, col]:                    
                    case Constants.TIBERIUM:
                        ch = 'T'
                    case Constants.CRYSTAL:
                        ch = 'C'
                match self.__building[row, col]:
                    case Constants.ACCU:
                        ch = 'A'
                    case Constants.POWERPLANT:
                        ch = 'P'                    
                s += ch + ' '
            s += '\n'
        return s