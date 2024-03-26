import gc
from iotfx.device import print_all as print_board_info

# enable garbage collection
gc.enable()
gc.collect()

print_board_info()

gc.collect()

# TODO: check device last reset reason and report it