import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as anim

MAX_X_POINTS = 20
UPDATE_INTERVAL_MS = 150

def read_y_data():
	return np.random.randn(1)

# Create the empty figure

fig = plt.figure()  
sub = fig.add_subplot(111, xlim=(-1, 1), ylim=(-1, 1))
PLOT, = sub.plot([],[])

# Called on each frame of the animation
def animate(i):
	xdata = PLOT.get_xdata()
	ydata = PLOT.get_ydata()
	newx = np.append(xdata, ((len(xdata)+1)*UPDATE_INTERVAL_MS)/1000 )
	newy = np.append(ydata, read_y_data())

	x_start = len(newx) - MAX_X_POINTS if len(newx) > MAX_X_POINTS else 0

	sub.clear()
	sub.plot(newx[x_start:], newy[x_start:])
	PLOT.set_data(newx, newy )
	plt.ylabel('Hue')
	plt.xlabel('Seconds')
	return PLOT,

ani = anim.FuncAnimation(fig, animate, interval=UPDATE_INTERVAL_MS, blit=False)
plt.show()