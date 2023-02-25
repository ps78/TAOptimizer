import re
from urllib import request
from urllib.parse import urlparse, unquote, quote
from game_mechanics import PowerField, Constants

class CncTaOptParser:
    """
    Class which provides methods to read a CncTaOpt-url and parse the 
    layout from the url-query parameter
    """    
    BASE_URL = "https://www.cnctaopt.com/index.html"

    # Coordinates of the tiberium fields, stored as list
    tiberium_coords = None

    # Coordinates of the crystal fields, stored as list
    crystal_coords = None

    # Coordinates of the accumulators, stored as list
    accu_coords = None

    # Coordinates of power plants, stored as list
    powerplant_coords = None

    def __init__(self, url): 
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
        self.tiberium_coords = list()
        self.crystal_coords = list()
        self.accu_coords = list()
        self.powerplant_coords = list()
        self.parse(url)

    def parse(self, url):
        """
        Parses the given url, also called by the constructor
        """
        self.tiberium_coords.clear()
        self.crystal_coords.clear()
        self.accu_coords.clear()
        self.powerplant_coords.clear()

        response = request.urlopen(url)
        if response.getcode() != 200:
            print("Error reading url")

        query = unquote(urlparse(response.url).query)
        params = query.split('~')

        layout_par = params[4]

        tokens = re.findall('\d+[a-z]|c|t|\\.', layout_par)
        row = 0
        col = 0
        for token in tokens[:Constants.BASE_COLUMNS*Constants.BASE_ROWS]:            
            match token[-1]:
                case 'c' | 'n':
                    self.crystal_coords.append((row, col))
                case 't' | 'j':
                    self.tiberium_coords.append((row, col))
                case 'a':
                    self.accu_coords.append((row, col))
                case 'p':
                    self.powerplant_coords.append((row, col))
            
            if col == Constants.BASE_COLUMNS-1:
                row += 1
                col = 0
            else:
                col += 1

            if row == Constants.BASE_ROWS:
                break

    def generate_url(self):

        # create empty defense and offense layout strings    
        defense_layout_str = '.' * (Constants.BASE_ROWS * Constants.BASE_COLUMNS)
        offense_layout_str = '.' * (Constants.BASE_OFFENSE_ROWS * Constants.BASE_COLUMNS)

        # create base layout string
        base_layout = [Constants.BASE_COLUMNS * ['.'] for i in range(Constants.BASE_ROWS)]        
        for c in self.tiberium_coords:
            base_layout[c[0]][c[1]] = "t"
        for c in self.crystal_coords:
            base_layout[c[0]][c[1]] = "c"
        for c in self.accu_coords:
            base_layout[c[0]][c[1]] = "65a"
        for c in self.powerplant_coords:
            base_layout[c[0]][c[1]] = "65p"
        base_layout_str = "".join(["".join(base_layout[i]) for i in range(Constants.BASE_ROWS)])

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

    def assign(self, pf :PowerField):
        self.tiberium_coords.clear()
        self.crystal_coords.clear()
        self.accu_coords.clear()
        self.powerplant_coords.clear()

        for row in range(Constants.BASE_ROWS):
            for col in range(Constants.BASE_COLUMNS):
                match pf.resource[row,col]:
                    case PowerField.TIBERIUM:
                        self.tiberium_coords.append((row,col))
                    case PowerField.CRYSTAL:
                        self.crystal_coords.append((row, col))
                    
                match pf.building[row, col]:
                    case PowerField.ACCU:
                        self.accu_coords.append((row, col))
                    case PowerField.POWERPLANT:
                        self.powerplant_coords.append((row, col))
                    