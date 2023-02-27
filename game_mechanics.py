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
    HARVESTER = 16
    SILO = 32
    REFINERY = 64
    CONSTRUCTIONYARD = 128
    DEFENSEHQ = 256
    DEFENCEFACILITY = 512
    COMMANDCENTER = 1024
    BARRACKS = 2048
    AIRFIELD = 4096
    FACTORY = 8192
    SKYSTRIKE = 16384
    IONCANNON = 32768
    FALCONSUPPORT = 65536

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

    @staticmethod
    def create_field(dtype = np.int32):
        """
        Creates a zero-ed 2D numpy array with the given dtype. Dimensions are
        taken from the Constants BASE_ROWS/COLUMNS
        """
        return np.zeros((Constants.BASE_ROWS, Constants.BASE_COLUMNS), dtype=dtype)

class PowerPlantFieldCategory:
    """
    This type is used by class Layout to store records representing
    a category of fields where power plants can be placed. The attributes are:
    - num_accus :int    Number of accumulators adjacient to the field
    - num_crystal :int  Number of crystal fields adjacient to the field
    - num_field :int    Total number of fields of this category in the layout
    - power_rate :int   Power production rate per hour of one field of this category
    """
    def __init__(self, rate :int, num_fields :int, coords :npt.ArrayLike):
        self.rate :int = rate
        self.num_fields :int = num_fields
        if coords is not None:
            self.coords :np.ndarray = coords if type(coords) is np.ndarray else np.array(coords, dtpye=np.int32)
        else:
            self.coords :np.ndarray = None

    def __str__(self):
        return f"{self.rate:,}/h - {self.num_fields} fields"

class BaseLayout:
    """
    Class that stores information of a base and provides means to manipulate it
    Most information is stored in 2D-numpy arrays to speed up calculations
    """
    @property
    def resource(self) -> np.ndarray:
        """
        A field showing 0 at coordinates without resources
        and TIBERIUM or CRYSTAL if there are resources
        """
        return self.__resource

    @property
    def field(self) -> np.ndarray:
        """
        A field showing the building at each coordinate
        """
        return self.__field

    @property
    def potential_power_rate(self) -> np.ndarray:
        """
        2D numpy array with total theoretical power production rate on every field
        in case a power plant is placed there

        Parameters:
            - copy_from_array : optional 2D numpy array containing the contents of the 
                                base encoded with the proper int-constants
        """
        return self.__potential_power_rate

    def __init__(self, copy_from_array :np.ndarray = None):
        self.__adjacent_crystal = Constants.create_field()
        self.__adjacent_accu = Constants.create_field()        
        self.__potential_power_rate = Constants.create_field(np.int64)
        self.__field = Constants.create_field()        
        if copy_from_array is not None:
            self.assign(copy_from_array)
        else:
            self._refresh_potential_power_rate()

    def assign(self, copy_from_array :np.ndarray):
        self.__field = np.copy(copy_from_array)

        self.__adjacent_crystal = Constants.create_field()
        for coord in np.argwhere(self.__field == Constants.CRYSTAL):        
            for c in self.enumerate_adjacent_coords(self.__field, coord):
                self.__adjacent_crystal[c[0], c[1]] += 1

        self.__adjacent_accu = Constants.create_field()
        for coord in np.argwhere(self.__field == Constants.ACCU):
            for c in self.enumerate_adjacent_coords(self.__field, coord):
                self.__adjacent_accu[c[0], c[1]] += 1

        self._refresh_potential_power_rate()

    @staticmethod
    def enumerate_adjacent_coords(arr :np.ndarray, coord :npt.ArrayLike) -> np.ndarray:
        """
        Enumerates the coordinates of the 3x3 field with coord in the center, 
        but does not return the center coordinate.
        If this 3x3 crosses the border of the given array, coordinates are skipped

        Parameters:
            - arr   : 2D numpy array
            - coord : 2D numpy array or compatible with 2 elements defining the
                    center coordinate

        Returns:
            - 2D numpy array of shape 8x2 in general potentially smaller depending on arr
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
                if r != row or c != col:
                    coords[idx] = (r,c)
                    idx += 1
        return coords

    def count_fields(self, field_type :int, coords :np.ndarray=None) -> int:
        """
        Counts how many fields of the given type are in the base. If coords
        is provided, only these coordinates are considered

        Parameters:
            - field_type : Constants-type of the field
            - coords : optional 2D numpy array with the coordinates to consider

        Returns:
            - Number of fields with the given type
        """
        if coords is None:
            return np.sum(self.__field & field_type != 0)
        else:
            return np.sum(self.__field[coords[:,0], coords[:,1]] & field_type != 0)

    def set(self, field_type :int, coords :np.ndarray, overlay :bool = False):
        """
        Sets the given field_type at all the coordinates

        Parameters:
            - field_type: what to set. Can be EMPTY to clear the fields
            - coords: one or more coordinates arranged in a 2D numpy array
            - overlay: if true, the given field_type is added to the existing field
                        use this e.g. to place harvesters
        """                
        before = np.copy(self.__field)        

        if len(coords.shape) == 1:
            coords = np.array([coords])

        if overlay:
            self.__field[coords[:,0], coords[:,1]] |= field_type
        else:
            self.__field[coords[:,0], coords[:,1]] = field_type

        need_power_rate_refresh :bool = False

        delta_crystal = (self.__field & Constants.CRYSTAL != 0).astype(int) - (before & Constants.CRYSTAL != 0).astype(int)
        for coord in np.argwhere(delta_crystal != 0):
            need_power_rate_refresh = True
            for c in self.enumerate_adjacent_coords(self.__field, coord):
                self.__adjacent_crystal[c[0], c[1]] += delta_crystal[c[0], c[1]]

        delta_accu = (self.__field & Constants.ACCU != 0).astype(int) - (before & Constants.ACCU != 0).astype(int)
        for coord in np.argwhere(delta_accu != 0):
            need_power_rate_refresh = True
            for c in self.enumerate_adjacent_coords(self.__field, coord):
                self.__adjacent_accu[c[0], c[1]] += delta_accu[coord[0], coord[1]]

        if need_power_rate_refresh:
            self._refresh_potential_power_rate()

    def set_optimal_powerplants(self, num_powerplants :int):
        """
        Places the given number of power plants in the optimal positions (in terms of 
        power production rate)

        Parameters:
            - num_powerplants: number of power plants to place
        """
        categories = self.get_power_field_categories(num_powerplants)
        for cat in categories:
            self.__field[cat.coords[:,0], cat.coords[:,1]] = Constants.POWERPLANT

    def _refresh_potential_power_rate(self):
        """
        Recalculates the potential power production rate array
        """
        self.__potential_power_rate = self.__adjacent_crystal * Constants.CRYSTAL_POWER_RATE + \
                        self.__adjacent_accu * Constants.ACCU_POWER_RATE + \
                        (self.__adjacent_accu >= 1) * Constants.ACCU_POWER_BONUS + \
                        Constants.BASE_POWER_RATE
    
    def get_power_field_categories(self, power_plant_limit :int = -1) -> list[PowerPlantFieldCategory]:
        """
        Returns a list with one entry per field category. All empty fields of the 
        base are categorized by the power production rate of a power plant that
        is placed there.
        The list is ordered with the highest production rate first

        Parameters:
            - power_plant_limit: maximum number of power plants to place. If -1: limited only 
                                 by the number of empty fields
        """
        categories : dict[int, PowerPlantFieldCategory] = dict()
        mask = (self.__field == Constants.EMPTY).astype(int)
        for row in range(Constants.BASE_ROWS):
            for col in range(Constants.BASE_COLUMNS):
                if self.__field[row, col] == Constants.EMPTY:
                    rate = self.__potential_power_rate[row, col]
                    if rate not in categories.keys():
                        coords = np.argwhere(self.__potential_power_rate * mask == rate)
                        categories[rate] = PowerPlantFieldCategory(rate, num_fields=coords.shape[0], coords=coords)

        # sort by rate, descending
        sorted_categories :list[tuple[int,PowerPlantFieldCategory]] = sorted(categories.items(), key=lambda x: x[0], reverse=True)
        if power_plant_limit == -1:
            return [cat[1] for cat in sorted_categories]
        else:
            result = []
            pp_left = power_plant_limit
            for cat in sorted_categories:
                if pp_left > cat[1].num_fields:
                    pp_left -= cat[1].num_fields
                    result.append(cat[1])
                else:
                    result.append(PowerPlantFieldCategory(cat[1].rate, pp_left, cat[1].coords[:pp_left]))
                    break
            return result

    def get_total_power_rate(self, powerplants :int) -> int:
        """
        Calculates the power production rate of the base if the given numer of power plants
        are placed in the optimal positions (without actually placing them)

        Parameters:
            - powerplants : number of power plants to place

        Returns:
            - Hourly power production rate
        """
        return sum([int(cat.rate)*int(cat.num_fields) for cat in self.get_power_field_categories(powerplants)])

    def get_empty_fields(self):
        """
        Returns an array with all base coordinates that are empty

        Returns:
            - 2D-numpy array, every row contains a coordinate
        """
        return np.argwhere(self.__field == Constants.EMPTY)

    def __str__(self):
        """
        String-representation of the base, showing a 2D matrix with a letter for each 
        resource/buiding type
        """
        s = ""
        for row in range(Constants.BASE_ROWS):
            for col in range(Constants.BASE_COLUMNS):
                ch = '.'
                match self.__field[row, col]:                    
                    case Constants.TIBERIUM:
                        ch = 'T'
                    case Constants.CRYSTAL:
                        ch = 'C'                
                    case Constants.ACCU:
                        ch = 'A'
                    case Constants.POWERPLANT:
                        ch = 'P'                    
                s += ch + ' '
            s += '\n'
        return s