import sys

FN = sys.argv[1]

newline = "\r\n"

with open(FN, "r") as f:
    lines = f.readlines()

if "\r" not in lines[0]:
    newline = "\n"

for idx, line in enumerate(lines):
    line = line.replace("delay(", "_delay_ms(")
    line = line.replace("strip.show(", "_show(")
    lines[idx] = line

for idx, line in enumerate(lines):
    if "#include" in line:
        lines.insert(idx+1, "#include <util/delay.h>"+newline)
        break

for idx, line in enumerate(lines):
    if "strip.begin" in line:
        lines.insert(idx, "Serial.begin(9600);"+newline)
        break


for idx, line in enumerate(lines):
    if "Adafruit_NeoPixel" in line and "strip" in line:
        lines.insert(
            idx+1, 'void _show() { Serial.println("---"); for (int i = 0; i < NUM_LEDS; i++) { Serial.print(strip.getPixelColor(i)); Serial.println("");}}'+newline)
        break

for line in lines:
    print(line, end="")
