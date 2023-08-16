from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import collections

MAX_X_POINTS = 20
UPDATE_INTERVAL_MS = 150

def read_y_data():
	return np.random.randn(1)

# Create the empty figure
def animate(i):
    y = read_y_data()
    data.append((datetime.now(), y))
    ax.relim()
    ax.autoscale_view()
    ax.set_ylim(-5, 5)
    ax.set_xlim(data[0][0], data[-1][0])
    line.set_data(*zip(*data))

fig, ax = plt.subplots()
x = datetime.now()
y = read_y_data()
data = collections.deque([(x, y)], maxlen=MAX_X_POINTS)
line, = plt.plot(*zip(*data), c='black')

ani = anim.FuncAnimation(fig, animate, interval=UPDATE_INTERVAL_MS)
plt.show()



# fig = plt.figure()  
# fig, ax = plt.subplots()
# sub = fig.add_subplot(111, xlim=(-1, 1), ylim=(-10, 10))
# PLOT, = sub.plot(x_data,y_data)

# # Called on each frame of the animation
# def animate(i):
# 	# xdata = PLOT.get_xdata()
# 	# ydata = PLOT.get_ydata()

# 	x_data.popleft()
# 	y_data.popleft()

# 	x_data.append(x_data[-1]+1)
# 	y_data.append(read_y_data())

# 	print(x_data)
# 	sub.clear()
# 	PLOT.set_data(x_data, y_data)
# 	sub.plot(x_data, y_data)

# 	plt.ylabel('Hue')
# 	plt.show()
# 	return PLOT,

# ani = anim.FuncAnimation(fig, animate, interval=UPDATE_INTERVAL_MS, blit=False)
# plt.show()