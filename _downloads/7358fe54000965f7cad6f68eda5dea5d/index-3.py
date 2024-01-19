fig, ax = plt.subplots(tight_layout=True)
x = np.linspace(0, 2*np.pi, 1024)

for i, (lw, c) in enumerate(zip(range(4), ['r', 'g', 'b', 'k'])):
   ax.plot(x, np.sin(x - i * np.pi / 4),
           label=r'$\phi = {{{0}}} \pi / 4$'.format(i),
           lw=lw + 1,
           c=c)

ax.set_xlim([0, 2*np.pi])
ax.set_title(r'$y=\sin(\theta + \phi)$')
ax.set_ylabel(r'[arb]')
ax.set_xlabel(r'$\theta$ [rad]')

ax.legend(loc=0)