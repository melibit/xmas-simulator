import socket
import subprocess
import pathlib
import random
import shutil
import time
import threading


def preprocess(src):
    newline = "\r\n"

    if "\r" not in src[0]:
        newline = "\n"

    for idx, line in enumerate(src):
        line = line.replace("delay(", "_delay_ms(")
        line = line.replace("strip.show(", "_show(")
        src[idx] = line

    for idx, line in enumerate(src):
        if "#include" in line:
            src.insert(idx+1, "#include <util/delay.h>"+newline)
            break

    for idx, line in enumerate(src):
        if "strip.begin" in line:
            src.insert(idx, "Serial.begin(9600);"+newline)
            break

    for idx, line in enumerate(src):
        if "Adafruit_NeoPixel" in line and "strip" in line:
            src.insert(
                idx+1, 'void _show() { Serial.println("---"); for (int i = 0; i < NUM_LEDS; i++) { Serial.print(strip.getPixelColor(i)); Serial.println("");}}'+newline)
            break

    return src


def compile(src):
    rand = random.randint(0, 2**32)
    pathlib.Path(
        f"./emu-server-build/{rand}-emu").mkdir(parents=True, exist_ok=True)
    with open(f"./emu-server-build/{rand}-emu/{rand}-emu.ino", "w") as f:
        f.writelines(preprocess(src))
    subprocess.run(
        ["arduino-cli", "compile", "-b", "arduino:avr:uno", "-e", f"./emu-server-build/{rand}-emu/"])
    with open(f"./emu-server-build/{rand}-emu/build/arduino.avr.uno/{rand}-emu.ino.elf", "rb") as f:
        elf = f.read()
    shutil.rmtree(pathlib.Path(f"./emu-server-build/{rand}-emu"))
    return elf


def run(elf, port=8412):
    rand = random.randint(0, 2**32)
    with open(f"./emu-server-build/{rand}-run.elf", "wb") as f:
        f.write(elf)
    process = subprocess.Popen(["qemu-system-avr", "-M", "uno", "-nographic", "-bios", f"./emu-server-build/{
        rand}-run.elf", "-serial", f"tcp::{port},server=on", "-D", f"./emu-server-build/{rand}-run.log", "-d", "in_asm"])
    return (process, port, rand, time.time())


processes = dict()


def kill_process(process, port, rand, t):
    print(f"killing {process} on {port} (id: {rand})")
    process.kill()
    pathlib.Path(f"./emu-server-build/{rand}-run.elf").unlink()
    if port in processes:
        del processes[port]


def time_thread():
    while True:
        time.sleep(1)
        if len(processes) > 0:
            print(processes)
        for process in list(processes.values()):
            if time.time() - process[-1] > 15*60:  # 15 minutes
                kill_process(*process)


thread = threading.Thread(target=time_thread)
thread.start()

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 5678               # Arbitrary non-privileged port
while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            print(processes)
            data = ""
            while True:
                rdata = conn.recv(1024)
                data += rdata.decode("utf-8")
                if data.endswith("EOF"):
                    data = data.removesuffix("EOF")
                    src = [e+'\n' for e in data.split('\n') if e]

                    elf = compile(src)
                    RUNPORT = random.randint(6000, 7000)
                    conn.sendall(bytes(str(RUNPORT), "utf-8"))
                    print("SENT:", bytes(str(RUNPORT), "utf-8"))
                    qemu = run(elf, RUNPORT)
                    processes[RUNPORT] = qemu

                if data.endswith("CLOSEPORT"):
                    data = data.removesuffix("CLOSEPORT")
                    RUNPORT = int(data)
                    if RUNPORT in processes:
                        kill_process(*processes[RUNPORT])

                if not rdata:
                    break

"""
with open("xmas.ino", "r") as f:
    elf = compile(f.readlines())

p, _, r = run(elf)


time.sleep(5)

exit(p, _, r)
"""
