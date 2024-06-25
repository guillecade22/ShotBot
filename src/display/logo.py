from pathlib import Path
from demo_opts import get_device
from PIL import Image
import time
import os

def main():
    img_path = "/home/pi/Desktop/robot/display/shots.png"
    logo = Image.open(img_path).convert("RGBA")

    fff = Image.new(logo.mode, logo.size, (0, 0, 0, 255))  # Black background

    background = Image.new("RGBA", device.size, (0, 0, 0, 255))  # Initial black background
    
    # Initial position of the logo at the right side of the display
    posn = (device.width, (device.height - logo.height) // 2)
    
    try:
        while True:
            if (os.getppid() == 1):
                break
            # Clear the previous frame by filling background with black
            background.paste((0, 0, 0, 255), (0, 0, device.width, device.height))

            # Paste the logo at the current position on the background
            background.paste(logo, posn, logo)

            # Display the current frame
            device.display(background.convert(device.mode))
            
            # Move the logo horizontally towards the left
            posn = (posn[0] - 7 , posn[1])

            # If logo moves completely out of the screen from right to left, reset its position to the right
            if posn[0] < -logo.width:
                posn = (device.width, posn[1])

            time.sleep(0.05)  # Adjust delay as needed for smoother animation

    except KeyboardInterrupt:
        # Handle keyboard interrupt (Ctrl+C)
        print("Termination signal received (Ctrl+C). Exiting...")

    finally:
        # Cleanup code here, if any
        # For example, closing device connections or saving state
        pass


if __name__ == "__main__":
    try:
        device = get_device()
        main()
    except KeyboardInterrupt:
        pass
