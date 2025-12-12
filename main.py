import os
import sys


os.system("mkdir -p emu")
os.system(f"cp {sys.argv[1]} emu/emu.ino")
os.system("python3 preprocess.py emu/emu.ino > emu/emu.ino.preprocess")
os.system("mv emu/emu.ino.preprocess emu/emu.ino")
os.system("arduino-cli compile -b arduino:avr:uno -e emu/")

os.system("qemu-system-avr -M uno -nographic -bios emu/build/arduino.avr.uno/emu.ino.elf -serial tcp::8412,server=on -D qemu.log -d in_asm & python3 emu_client.py")
