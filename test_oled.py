import board
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import time

# Create I2C interface
# This uses the default I2C pins (SCL, SDA) on the Pi
try:
    i2c = board.I2C()  # uses board.SCL and board.SDA
except Exception as e:
    print(f"Error initializing I2C: {e}")
    exit(1)

# Create the SSD1306 OLED class
# Change to (128, 32) if you have a 32-pixel-tall display
try:
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
except Exception as e:
    print(f"Error initializing OLED: {e}")
    exit(1)

# Clear display
oled.fill(0)
oled.show()

# Create blank image for drawing
image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()

# Draw text
text1 = "IP Monitor"
text2 = "192.168.1.100"  # Example IP address
draw.text((0, 0), text1, font=font, fill=255)
draw.text((0, 20), text2, font=font, fill=255)

# Display image
oled.image(image)
oled.show()

time.sleep(5)  # Keep the message on screen for 5 seconds

# Optionally clear the display after test
oled.fill(0)
oled.show() 