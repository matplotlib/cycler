from cycler import cycler
from itertools import cycle

fig, (ax1, ax2) = plt.subplots(1, 2, tight_layout=True,
                               figsize=(8, 4))
x = np.arange(10)

color_cycle = cycler(c=['r', 'g', 'b'])
ls_cycle = cycler('ls', ['-', '--'])
lw_cycle = cycler('lw', range(1, 4))

sty_cycle = ls_cycle * (color_cycle + lw_cycle)

for i, sty in enumerate(sty_cycle):
   ax1.plot(x, x*(i+1), **sty)

sty_cycle = (color_cycle + lw_cycle) * ls_cycle

for i, sty in enumerate(sty_cycle):
   ax2.plot(x, x*(i+1), **sty)