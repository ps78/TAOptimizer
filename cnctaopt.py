import re
from urllib import request
from urllib.parse import urlparse, unquote, quote
from game_mechanics import BaseLayout, Constants
import numpy as np

class CncTaOptParser:
    """
    Class which provides methods to read a CncTaOpt-url and parse the 
    layout from the url-query parameter

    Parameters:
        - url: url from which to load this instance, optional
        - field: 2D numpy array from which to load this instance, optional
    """    
    BASE_URL = "https://www.cnctaopt.com/index.html"

    @property
    def field(self) -> np.ndarray:
        return np.copy(self.__field)

    def __init__(self, url :str=None, field :np.ndarray=None): 
        """
        Constructor, reads the given url and populates the tib/crystal coordinates
        """
        self.version = 3 # cnctaopt version, currently always 3
        self.base_name = "base"
        self.base_faction = "G" # {G, N, F, E} for GDI, NOD, Forgotten, Unknown
        self.offense_faction = "G" # {G, N, F, E}
        self.economy = "new"    
        self.world_id = 341
        self.world_name = "Tiberian 13"
        self.max_level = 65
        self.x_coord = 550
        self.y_coord = 550
        
        if field is not None:
            self.assign(field)
        else:
            self.__field = Constants.create_field()

        if url is not None:
            self.parse(url)

    def assign(self, field :np.ndarray):
        self.__field = field

    def parse(self, url):
        """
        Parses the given url, also called by the constructor
        """
        response = request.urlopen(url)
        if response.getcode() != 200:
            print("Error reading url")

        query = unquote(urlparse(response.url).query)
        params = query.split('~')

        layout_par = params[4]

        tokens = re.findall('\d+[a-z]|c|t|\\.', layout_par)
        row, col = 0, 0
        for token in tokens[:Constants.BASE_COLUMNS*Constants.BASE_ROWS]:            
            match token[-1]:
                case 'c' | 'n':
                    self.__field[row, col] = Constants.CRYSTAL
                case 'n':
                    self.__field[row, col] = Constants.CRYSTAL | Constants.HARVESTER
                case 't':
                    self.__field[row, col] = Constants.TIBERIUM
                case 'j':
                    self.__field[row, col] = Constants.TIBERIUM | Constants.HARVESTER
                case 'a':
                    self.__field[row, col] = Constants.ACCU
                case 'p':
                    self.__field[row, col] = Constants.POWERPLANT
                case _:
                    self.__field[row, col] = Constants.EMPTY
            
            if col == Constants.BASE_COLUMNS-1:
                row += 1
                col = 0
            else:
                col += 1
            if row == Constants.BASE_ROWS:
                break

    def generate_url(self):
        """
        Generates an URL to cncTAopt which contains all information of the instance in 
        the query parameters of the url
        """
        # create base layout string
        base_layout_str = ''
        for row in range(Constants.BASE_ROWS):
            for col in range(Constants.BASE_COLUMNS):
                match self.__field[row, col]:
                    case Constants.TIBERIUM:
                        base_layout_str += 't'
                    case Constants.CRYSTAL:
                        base_layout_str += 'c'
                    case Constants.ACCU:
                        base_layout_str += '65a'
                    case Constants.POWERPLANT:
                        base_layout_str += '65p'

        # create empty defense and offense layout strings    
        defense_layout_str = '.' * (Constants.BASE_ROWS * Constants.BASE_COLUMNS)
        offense_layout_str = '.' * (Constants.BASE_OFFENSE_ROWS * Constants.BASE_COLUMNS)

        # define the query parameters of the url        
        query_pars = list()
        query_pars.append(f"ver={self.version}")
        query_pars.append(self.base_faction)
        query_pars.append(self.offense_faction)
        query_pars.append(self.base_name)
        query_pars.append(base_layout_str+defense_layout_str+offense_layout_str)
        query_pars.append(f"E={self.economy}")
        query_pars.append(f"X={self.x_coord}")
        query_pars.append(f"Y={self.y_coord}")
        query_pars.append(f"WID={self.world_id}")
        query_pars.append(f"WN={self.world_name}")
        query_pars.append(f"ML={self.max_level}")
        
        return self.BASE_URL + '?' + '~'.join([quote(par) for par in query_pars])