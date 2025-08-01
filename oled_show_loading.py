#!/usr/bin/env python3
"""
Displays "Loading..." on the OLED screen.
Intended to be run as an early-boot systemd service.
"""
try:
    import board
    import adafruit_ssd1306
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    # Exit silently if libraries are not available for any reason
    exit()

def show_loading_message():
    """Initializes the OLED and displays a centered 'Loading...' message."""
    try:
        i2c = board.I2C()  # Default SCL, SDA
        oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

        # Prepare to draw
        image = Image.new("1", (oled.width, oled.height))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        
        # Center the text
        text = "Loading..."
        if hasattr(font, 'getbbox'):
            bbox = font.getbbox(text)
            textwidth = bbox[2] - bbox[0]
            textheight = bbox[3] - bbox[1]
        else:
            textwidth, textheight = draw.textsize(text, font=font)
        
        x = (oled.width - textwidth) // 2
        y = (oled.height - textheight) // 2
        
        # Clear display, draw text, and show it
        oled.fill(0)
        draw.text((x, y), text, font=font, fill=255)
        oled.image(image)
        oled.show()

    except Exception:
        # If there's any error (e.g., OLED not connected), exit silently.
        # We don't want to hang the boot process.
        pass

if __name__ == "__main__":
    show_loading_message() 