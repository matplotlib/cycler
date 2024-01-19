from cycler import cycler
from itertools import cycle

fig, (ax1, ax2) = plt.subplots(1, 2, tight_layout=True,
                               figsize=(8, 4))
x = np.arange(10)

color_cycle = cycler(c=['r', 'g', 'b'])

for i, sty in enumerate(color_cycle):
   ax1.plot(x, x*(i+1), **sty)


for i, sty in zip(range(1, 5), cycle(color_cycle)):
   ax2.plot(x, x*i, **sty)