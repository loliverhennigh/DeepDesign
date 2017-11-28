
import sys

# import latnet librarys
sys.path.append('../deepdesign')
from controller import DesignController

data_script = "./heat_sink_generator"



ctr = DesignController(data_script=data_script)
ctr

