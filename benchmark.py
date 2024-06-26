
'''Running this file will play out a starcraft game using the settings from run_locally.py
and open up a profile viewer (snakeviz) of the game once its done.'''
#install snakeviz if don't have it already (or can use built in pstats module, or other profile viewer)
import os

os.system("python -O -m cProfile -o profile_name.prof run_locally.py")
os.system("snakeviz profile_name.prof")