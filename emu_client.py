import matplotlib.pyplot as plt
import socket
import csv
import time
global RUNPORT, cid

HOST = input("Enter emu server Hostname: ")

PORT = 5678
while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            print(f"Attempting to connect to {HOST}:{PORT}")
            s.connect((HOST, PORT))
        except ConnectionRefusedError:
            time.sleep(1)
            continue
        print("Connection Successsful")
        with open("xmas.ino", "rb") as f:
            s.sendfile(f)
        print("Uploaded File")
        s.sendall(bytes("EOF", "utf-8"))
        data = s.recv(1024)
        RUNPORT = int(str(data, "utf-8"))
        break

leds = list()
buf = ""


FN = "led_xyz.csv"
data = list(csv.reader(open(FN), delimiter=","))

xs = list()
ys = list()
zs = list()

for _x, _y, _z in data[1:]:
    x = float(_x)
    y = float(_y)
    z = float(_z)
    xs.append(x)
    ys.append(z)
    zs.append(y)


fig = plt.figure()


def on_close(event):
    global RUNPORT, cid
    fig.canvas.mpl_disconnect(cid)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            print(f"Attempting to connect to {HOST}:{PORT}")
            s.connect((HOST, PORT))
        except ConnectionRefusedError:
            exit()
        print("Connection Successsful")
        s.sendall(bytes(f"{RUNPORT}CLOSEPORT", "utf-8"))
    exit()


ax = fig.add_subplot(projection='3d')
ax.set_aspect('equal')

cid = fig.canvas.mpl_connect('close_event', on_close)

ax.set_title(FN)
fig.canvas.manager.set_window_title(FN)
ax.set_xlabel(data[0][0])
ax.set_ylabel(data[0][2])
ax.set_zlabel(data[0][1])
plt.ion()
plt.show()
scatter = None

while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            print(f"Attempting to connect to {HOST}:{RUNPORT}\n")
            s.connect((HOST, RUNPORT))
        except ConnectionRefusedError:
            time.sleep(1)
            continue

        print("Connection Successful")

        while True:
            data = s.recv(1024)
            for c in data:
                if chr(c) == "-":
                    if len(leds) >= len(xs):
                        if scatter is not None:
                            scatter.remove()
                        scatter = ax.scatter(xs, ys, zs, marker='o',
                                             c=[[(((x // 256) // 256) % 256)/256, ((x // 256) % 256)/256, (x % 256)/256] for x in leds[:len(xs)-len(leds)]])
                        plt.pause(.1)
                    leds = list()
                    continue

                if chr(c) == '\r' or chr(c) == '\n':
                    if len(buf) > 0:
                        leds.append(int(buf))
                    buf = ""
                    continue

                buf += chr(c)
