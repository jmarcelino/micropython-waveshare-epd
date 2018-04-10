import pycom
pycom.heartbeat(False)

from machine import Pin
import epd7in5b
#import imagedata640
import font12
import font20
import framebuf

reset = Pin('P19')
dc = Pin('P20')
busy = Pin('P18')
cs = Pin('P4')
clk = Pin('P21')
mosi = Pin('P22')

epd = epd7in5b.EPD7IN5B(reset, dc, busy, cs, clk, mosi)
epd.init()
epd.clear_frame()

# For simplicity, the arguments are explicit numerical coordinates
epd.draw_rectangle(10, 60, 50, 110, epd7in5b.COLORED)
epd.draw_line(10, 60, 50, 110, epd7in5b.COLORED)
epd.draw_line(50, 60, 10, 110, epd7in5b.COLORED)
epd.draw_circle(120, 80, 30, epd7in5b.COLORED)
epd.draw_filled_rectangle(10, 130, 50, 180, epd7in5b.COLORED)
epd.draw_filled_rectangle(0, 6, 200, 26, epd7in5b.COLORED)
epd.draw_filled_circle(120, 150, 30, epd7in5b.COLORED)

# write strings to the buffer
epd.display_string_at(48, 10, "e-Paper Demo", font12, epd7in5b.UNCOLORED)
epd.display_string_at(20, 30, "Hello Pycom!", font20, epd7in5b.COLORED)
# display the frame
epd.display_frame()

# Call sleep to enter power saving mode
#epd.sleep()

# To wake up the display from power saving mode, call init() again
#epd.init()

epd.set_rotate(epd7in5b.ROTATE_0)
epd.clear_frame()
epd.draw_bmp('/flash/gfx/pycomLogo1bpp.bmp', epd7in5b.UNCOLORED)
epd.display_frame()

# You can import frame buffer directly:
#epd.display_frame(epd.get_frame_buffer(imagedata640.MONOCOLOR_BITMAP), None)

epd.clear_frame()

# You can also draw 1-color bitmaps in Windows BMP format
epd.set_rotate(epd7in5b.ROTATE_0)
epd.clear_frame()
epd.draw_bmp('/flash/gfx/aykm200.bmp', epd7in5b.COLORED)
epd.display_frame()

epd.set_rotate(epd7in5b.ROTATE_90)
#epd.clear_frame(frame_black)
epd.draw_bmp('/flash/gfx/aykm200.bmp', epd7in5b.COLORED)
epd.display_frame()

epd.set_rotate(epd7in5b.ROTATE_180)
#epd.clear_frame(frame_black)
epd.draw_bmp_at(10, 13, '/flash/gfx/happy180.bmp', epd7in5b.UNCOLORED)
epd.display_frame()

epd.set_rotate(epd7in5b.ROTATE_270)
#epd.clear_frame(frame_black)
epd.draw_bmp_at(10, 13, '/flash/gfx/happy180.bmp', epd7in5b.UNCOLORED)
epd.display_frame()

epd.set_rotate(epd7in5b.ROTATE_0)
epd.clear_frame()
epd.draw_bmp('/flash/gfx/pycom200_b.bmp', epd7in5b.COLORED)

epd.display_string_at(12, 188, "More at http://kapusta.cc", font12, epd7in5b.COLORED)
epd.display_frame()
