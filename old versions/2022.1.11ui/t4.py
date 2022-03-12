import numpy as np
from matplotlib.animation import FuncAnimation
import matplotlib.pylab as plt

reward = 0

def gen():
    global reward
    i = 0
    while reward <= 10:
        i += 1
        yield i

x =[]
y = []

def animate(i):
    global reward
    reward +=1
    # some_object[i] = func(reward)
    x.append(i)
    y.append(i)

    k = reward **2

    ax1.clear()
    ax1.plot(x, y)
    # plt.title(title)
    # plt.xlabel('Wavelength, nm')
    # plt.ylabel('Signal Amplitude, AU')

    print(i)
    # if i == 10:
    #     exit()
    # return msg


fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
# ani = animation.FuncAnimation(fig, animate, interval=1000)
anim = FuncAnimation(fig, animate, frames=gen, repeat = False)
plt.show()





