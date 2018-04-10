import utime
from machine import Pin, SPI
from bmp import BitmapHeader, BitmapHeaderInfo
import ustruct
import framebuf


# Display resolution
EPD_WIDTH       = 640
EPD_HEIGHT      = 384

# EPD1IN54B commands
PANEL_SETTING                               = const(0x00)
POWER_SETTING                               = const(0x01)
POWER_OFF                                   = const(0x02)
POWER_OFF_SEQUENCE_SETTING                  = const(0x03)
POWER_ON                                    = const(0x04)
POWER_ON_MEASURE                            = const(0x05)
BOOSTER_SOFT_START                          = const(0x06)
DEEP_SLEEP                                  = const(0x07)
DATA_START_TRANSMISSION_1                   = const(0x10)
DATA_STOP                                   = const(0x11)
DISPLAY_REFRESH                             = const(0x12)
DATA_START_TRANSMISSION_2                   = const(0x13)
PLL_CONTROL                                 = const(0x30)
TEMPERATURE_SENSOR_COMMAND                  = const(0x40)
TEMPERATURE_SENSOR_CALIBRATION              = const(0x41)
TEMPERATURE_SENSOR_WRITE                    = const(0x42)
TEMPERATURE_SENSOR_READ                     = const(0x43)
VCOM_AND_DATA_INTERVAL_SETTING              = const(0x50)
LOW_POWER_DETECTION                         = const(0x51)
TCON_SETTING                                = const(0x60)
TCON_RESOLUTION                             = const(0x61)
SOURCE_AND_GATE_START_SETTING               = const(0x62)
GET_STATUS                                  = const(0x71)
AUTO_MEASURE_VCOM                           = const(0x80)
VCOM_VALUE                                  = const(0x81)
VCM_DC_SETTING_REGISTER                     = const(0x82)
PROGRAM_MODE                                = const(0xA0)
ACTIVE_PROGRAM                              = const(0xA1)
READ_OTP_DATA                               = const(0xA2)
FLASH_MODE                                  = const(0xE5)

# Color or no color
COLORED = 4
UNCOLORED = 0

# Display orientation
ROTATE_0                                    = 0
ROTATE_90                                   = 1
ROTATE_180                                  = 2
ROTATE_270                                  = 3

class EPD7IN5B():
    def __init__(self, reset, dc, busy, cs, clk, mosi):

        # initialize the frame buffer
        self.buffer = bytearray(EPD_WIDTH * EPD_HEIGHT // 2)

        #setup framebuf.FrameBuffer
        self.fbuf = framebuf.FrameBuffer(self.buffer, EPD_WIDTH, EPD_HEIGHT, framebuf.GS4_HMSB)

        self.reset_pin = reset
        self.reset_pin.mode(Pin.OUT)

        self.dc_pin = dc
        self.dc_pin.mode(Pin.OUT)

        self.busy_pin = busy
        self.busy_pin.mode(Pin.IN)

        self.cs_pin = cs
        self.cs_pin.mode(Pin.OUT)
        self.cs_pin.pull(Pin.PULL_UP)

        self.spi = SPI(0, mode=SPI.MASTER, baudrate=2000000, polarity=0, phase=0, pins=(clk, mosi, None))

        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.rotate = ROTATE_0

    def init(self):
        self.reset()
        self.send_command(POWER_SETTING)
        self.send_data(0x37)
        self.send_data(0x00)
        self.send_command(PANEL_SETTING)
        self.send_data(0xCF)
        self.send_data(0x08)
        self.send_command(BOOSTER_SOFT_START)
        self.send_data(0xC7)
        self.send_data(0xCC)
        self.send_data(0x28)
        self.send_command(POWER_ON)

        self.wait_until_idle()

        self.send_command(PLL_CONTROL)
        self.send_data(0x3C)
        self.send_command(TEMPERATURE_SENSOR_CALIBRATION)
        self.send_data(0x00)
        self.send_command(VCOM_AND_DATA_INTERVAL_SETTING)
        self.send_data(0x77)
        self.send_command(TCON_SETTING)
        self.send_data(0x22)
        self.send_command(TCON_RESOLUTION)
        self.send_data(ustruct.pack(">HH", EPD_WIDTH, EPD_HEIGHT))
        self.send_command(VCM_DC_SETTING_REGISTER)
        self.send_data(0x1E)

        self.send_command(FLASH_MODE)
        self.send_data(0x03)

        return 0

    def _spi_transfer(self, data):
        self.cs_pin(False)
        self.spi.write(data)
        self.cs_pin(True)

    def delay_ms(self, delaytime):
        utime.sleep_ms(delaytime)

    def send_command(self, command):
        self.dc_pin(False)
        self._spi_transfer(command)

    def send_data(self, data):
        self.dc_pin(True)
        self._spi_transfer(data)

    def wait_until_idle(self):
        while(self.busy_pin() == False):      # 0: idle, 1: busy
            self.delay_ms(100)

    def reset(self):
        self.reset_pin(False)         # module reset
        self.delay_ms(200)
        self.reset_pin(True)
        self.delay_ms(200)

    def clear_frame(self):
        self.fbuf.fill(3)

    def get_frame_buffer(self, image):
        buf = bytearray(int(self.width * self.height / 4))

        for y in range(self.height):
            for x in range(self.width):
                # Set the bits for the column of pixels at the current position.
                if image[int((x + y * self.width) / 8)] & (0x80 >> (x % 8)):
                    buf[int((x + y * self.width) / 4)] &= ~(0xC0 >> (x % 4 * 2))
                else:
                    buf[int((x + y * self.width) / 4)] |= 0xC0 >> (x % 4 * 2)
                #
                #
                # if pixels[x, y] < 64:           # black
                #     buf[(x + y * self.width) / 4] &= ~(0xC0 >> (x % 4 * 2))
                # elif pixels[x, y] < 192:     # convert gray to red
                #     buf[(x + y * self.width) / 4] &= ~(0xC0 >> (x % 4 * 2))
                #     buf[(x + y * self.width) / 4] |= 0x40 >> (x % 4 * 2)
                # else:                           # white
                #     buf[(x + y * self.width) / 4] |= 0xC0 >> (x % 4 * 2)
        return buf

    def display_frame(self):
        self.send_command(DATA_START_TRANSMISSION_1)
        # for i in range(0, self.width / 4 * self.height):
        #     temp1 = self.buffer[i]
        #     j = 0
        #     while (j < 4):
        #         if ((temp1 & 0xC0) == 0xC0):
        #             temp2 = 0x03
        #         elif ((temp1 & 0xC0) == 0x00):
        #             temp2 = 0x00
        #         else:
        #             temp2 = 0x04
        #         temp2 = (temp2 << 4) & 0xFF
        #         temp1 = (temp1 << 2) & 0xFF
        #         j += 1
        #         if((temp1 & 0xC0) == 0xC0):
        #             temp2 |= 0x03
        #         elif ((temp1 & 0xC0) == 0x00):
        #             temp2 |= 0x00
        #         else:
        #             temp2 |= 0x04
        #         temp1 = (temp1 << 2) & 0xFF
        #         self.send_data(temp2)
        #         j += 1
        self.send_data(self.buffer)
        self.send_command(DISPLAY_REFRESH)
        self.delay_ms(100)
        self.wait_until_idle()

    # after this, call epd.init() to awaken the module
    def sleep(self):
        self.send_command(VCOM_AND_DATA_INTERVAL_SETTING)
        self.send_data(0x17)
        self.send_command(VCM_DC_SETTING_REGISTER)         #to solve Vcom drop
        self.send_data(0x00)
        self.send_command(POWER_SETTING)         #power setting
        self.send_data(0x02)        #gate switch to external
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.wait_until_idle()
        self.send_command(POWER_OFF)         #power off


    def set_rotate(self, rotate):
        if (rotate == ROTATE_0):
            self.rotate = ROTATE_0
            self.width = EPD_WIDTH
            self.height = EPD_HEIGHT
        elif (rotate == ROTATE_90):
            self.rotate = ROTATE_90
            self.width = EPD_HEIGHT
            self.height = EPD_WIDTH
        elif (rotate == ROTATE_180):
            self.rotate = ROTATE_180
            self.width = EPD_WIDTH
            self.height = EPD_HEIGHT
        elif (rotate == ROTATE_270):
            self.rotate = ROTATE_270
            self.width = EPD_HEIGHT
            self.height = EPD_WIDTH


    def set_pixel(self, x, y, colored):
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return
        if (self.rotate == ROTATE_0):
            self.fbuf.pixel(x, y, colored)
        elif (self.rotate == ROTATE_90):
            point_temp = x
            x = EPD_WIDTH - y
            y = point_temp
            self.fbuf.fbpixel(x, y, colored)
        elif (self.rotate == ROTATE_180):
            x = EPD_WIDTH - x
            y = EPD_HEIGHT- y
            self.fbuf.pixel(x, y, colored)
        elif (self.rotate == ROTATE_270):
            point_temp = x
            x = y
            y = EPD_HEIGHT - point_temp
            self.fbuf.pixel(x, y, colored)


    # def set_absolute_pixel(self, frame_buffer, x, y, colored):
    #     # To avoid display orientation effects
    #     # use EPD_WIDTH instead of self.width
    #     # use EPD_HEIGHT instead of self.height
    #     if (x < 0 or x >= EPD_WIDTH or y < 0 or y >= EPD_HEIGHT):
    #         return
    #     if (colored):
    #         #frame_buffer[int((x + y * EPD_WIDTH) / 8)] &= ~(0x80 >> (x % 8))
    #         frame_buffer[int((x + y * EPD_WIDTH) / 4)] &= ~(0xC0 >> (x % 4 * 2))
    #         frame_buffer[int((x + y * EPD_WIDTH) / 4)] |= 0x40 >> (x % 4 * 2)
    #     else:
    #         frame_buffer[int((x + y * EPD_WIDTH) / 4)] &= ~(0xC0 >> (x % 4 * 2))
    #         #frame_buffer[int((x + y * EPD_WIDTH) / 8)] |= 0x80 >> (x % 8)


    def draw_char_at(self, x, y, char, font, colored):
        char_offset = (ord(char) - ord(' ')) * font.height * (int(font.width / 8) + (1 if font.width % 8 else 0))
        offset = 0

        for j in range(font.height):
            for i in range(font.width):
                if font.data[char_offset+offset] & (0x80 >> (i % 8)):
                    self.set_pixel(x + i, y + j, colored)
                if i % 8 == 7:
                    offset += 1
            if font.width % 8 != 0:
                offset += 1


    def display_string_at(self, x, y, text, font, colored):
        refcolumn = x

        # Send the string character by character on EPD
        for index in range(len(text)):
            # Display one character on EPD
            self.draw_char_at(refcolumn, y, text[index], font, colored)
            # Decrement the column position by 16
            refcolumn += font.width


    def draw_line(self, x0, y0, x1, y1, colored):
        # Bresenham algorithm
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while((x0 != x1) and (y0 != y1)):
            self.set_pixel(x0, y0 , colored)
            if (2 * err >= dy):
                err += dy
                x0 += sx
            if (2 * err <= dx):
                err += dx
                y0 += sy


    def draw_horizontal_line(self, x, y, width, colored):
        for i in range(x, x + width):
            self.set_pixel(i, y, colored)


    def draw_vertical_line(self, x, y, height, colored):
        for i in range(y, y + height):
            self.set_pixel(x, i, colored)


    def draw_rectangle(self, x0, y0, x1, y1, colored):
        min_x = x0 if x1 > x0 else x1
        max_x = x1 if x1 > x0 else x0
        min_y = y0 if y1 > y0 else y1
        max_y = y1 if y1 > y0 else y0
        self.draw_horizontal_line(min_x, min_y, max_x - min_x + 1, colored)
        self.draw_horizontal_line(min_x, max_y, max_x - min_x + 1, colored)
        self.draw_vertical_line(min_x, min_y, max_y - min_y + 1, colored)
        self.draw_vertical_line(max_x, min_y, max_y - min_y + 1, colored)


    def draw_filled_rectangle(self, x0, y0, x1, y1, colored):
        min_x = x0 if x1 > x0 else x1
        max_x = x1 if x1 > x0 else x0
        min_y = y0 if y1 > y0 else y1
        max_y = y1 if y1 > y0 else y0
        for i in range(min_x, max_x + 1):
            self.draw_vertical_line(i, min_y, max_y - min_y + 1, colored)


    def draw_circle(self, x, y, radius, colored):
        # Bresenham algorithm
        x_pos = -radius
        y_pos = 0
        err = 2 - 2 * radius
        if (x >= self.width or y >= self.height):
            return
        while True:
            self.set_pixel(x - x_pos, y + y_pos, colored)
            self.set_pixel(x + x_pos, y + y_pos, colored)
            self.set_pixel(x + x_pos, y - y_pos, colored)
            self.set_pixel(x - x_pos, y - y_pos, colored)
            e2 = err
            if (e2 <= y_pos):
                y_pos += 1
                err += y_pos * 2 + 1
                if(-x_pos == y_pos and e2 <= x_pos):
                    e2 = 0
            if (e2 > x_pos):
                x_pos += 1
                err += x_pos * 2 + 1
            if x_pos > 0:
                break


    def draw_filled_circle(self, x, y, radius, colored):
        # Bresenham algorithm
        x_pos = -radius
        y_pos = 0
        err = 2 - 2 * radius
        if (x >= self.width or y >= self.height):
            return
        while True:
            self.set_pixel(x - x_pos, y + y_pos, colored)
            self.set_pixel(x + x_pos, y + y_pos, colored)
            self.set_pixel(x + x_pos, y - y_pos, colored)
            self.set_pixel(x - x_pos, y - y_pos, colored)
            self.draw_horizontal_line(x + x_pos, y + y_pos, 2 * (-x_pos) + 1, colored)
            self.draw_horizontal_line(x + x_pos, y - y_pos, 2 * (-x_pos) + 1, colored)
            e2 = err
            if (e2 <= y_pos):
                y_pos += 1
                err += y_pos * 2 + 1
                if(-x_pos == y_pos and e2 <= x_pos):
                    e2 = 0
            if (e2 > x_pos):
                x_pos  += 1
                err += x_pos * 2 + 1
            if x_pos > 0:
                break


    def draw_bmp(self, image_path, colored):
        self.draw_bmp_at(0, 0, image_path, colored)


    def draw_bmp_at(self, x, y, image_path, colored):
        if x >= self.width or y >= self.height:
            return

        try:
            with open(image_path, 'rb') as bmp_file:
                header = BitmapHeader(bmp_file.read(BitmapHeader.SIZE_IN_BYTES))
                header_info = BitmapHeaderInfo(bmp_file.read(BitmapHeaderInfo.SIZE_IN_BYTES))
                data_end = header.file_size - 2

                if header_info.width > self.width:
                    widthClipped = self.width
                elif x < 0:
                    widthClipped = header_info.width + x
                else:
                    widthClipped = header_info.width

                if header_info.height > self.height:
                    heightClipped = self.height
                elif y < 0:
                    heightClipped = header_info.height + y
                else:
                    heightClipped = header_info.height

                heightClipped = max(0, min(self.height-y, heightClipped))
                y_offset = max(0, -y)

                if heightClipped <= 0 or widthClipped <= 0:
                    return

                width_in_bytes = int(self.width/8)
                if header_info.width_in_bytes > width_in_bytes:
                    rowBytesClipped = width_in_bytes
                else:
                    rowBytesClipped = header_info.width_in_bytes

                for row in range(y_offset, heightClipped):
                    absolute_row = row + y
                    # seek to beginning of line
                    bmp_file.seek(data_end - (row + 1) * header_info.line_width)

                    line = bytearray(bmp_file.read(rowBytesClipped))
                    if header_info.last_byte_padding > 0:
                        mask = 0xFF<<header_info.last_byte_padding & 0xFF
                        line[-1] &= mask

                    for byte_index in range(len(line)):
                        byte = line[byte_index]
                        for i in range(8):
                            if byte & (0x80 >> i):
                                self.set_pixel(byte_index*8 + i + x, absolute_row, colored)

        except OSError as e:
            print('error: {}'.format(e))

### END OF FILE ###
