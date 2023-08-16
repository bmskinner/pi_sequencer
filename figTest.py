from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import collections

MAX_X_POINTS = 20
UPDATE_INTERVAL_MS = 150

def read_y_data():
	return np.random.randn(1)

# How to update the view
def animate(i):
    y = read_y_data()
    data.append((datetime.now(), y))
    ax.relim()
    ax.set_ylim(-5, 5)
    ax.set_xlim(data[0][0], data[-1][0])
    line.set_data(*zip(*data))

# Create the empty figure
fig, ax = plt.subplots()
x = datetime.now()
y = read_y_data()
data = collections.deque([(x, y)], maxlen=MAX_X_POINTS)
line, = plt.plot(*zip(*data), c='black')

ani = anim.FuncAnimation(fig, animate, interval=UPDATE_INTERVAL_MS)
plt.show()
