# *****************************************************************************
# * | File        :	  epd2in9_v2.py
# * | Author      :   Waveshare team / Antigravity
# * | Function    :   Electronic paper driver for SSD1680 (2.9" V2)
# *----------------
# * | This version:   V1.1-opi
# * | Date        :   2026-07-06
# * | Info        :   Adapted for Orange Pi RV2 & Mock Preview
# *****************************************************************************

import logging
from . import epdconfig

# Display resolution
EPD_WIDTH       = 128
EPD_HEIGHT      = 296
GRAY1  = 0xff #white
GRAY2  = 0xC0
GRAY3  = 0x80 #gray
GRAY4  = 0x00 #Blackest

logger = logging.getLogger(__name__)

class EPD:
    def __init__(self):
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.cs_pin = epdconfig.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.GRAY1  = GRAY1 #white
        self.GRAY2  = GRAY2
        self.GRAY3  = GRAY3 #gray
        self.GRAY4  = GRAY4 #Blackest
        
    WF_PARTIAL_2IN9 = [
    0x0,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x80,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x40,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0A,0x0,0x0,0x0,0x0,0x0,0x1,  
    0x1,0x0,0x0,0x0,0x0,0x0,0x0,
    0x1,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x22,0x22,0x22,0x22,0x22,0x22,0x0,0x0,0x0,
    0x22,0x17,0x41,0xB0,0x32,0x36,
    ]

    WS_20_30 = [									
    0x80,	0x66,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x40,	0x0,	0x0,	0x0,
    0x10,	0x66,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x20,	0x0,	0x0,	0x0,
    0x80,	0x66,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x40,	0x0,	0x0,	0x0,
    0x10,	0x66,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x20,	0x0,	0x0,	0x0,
    0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,
    0x14,	0x8,	0x0,	0x0,	0x0,	0x0,	0x2,					
    0xA,	0xA,	0x0,	0xA,	0xA,	0x0,	0x1,					
    0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,					
    0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,					
    0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,					
    0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,					
    0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,					
    0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,					
    0x14,	0x8,	0x0,	0x1,	0x0,	0x0,	0x1,					
    0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x1,					
    0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,					
    0x0,	0x0,	0x0,	0x0,	0x0,	0x0,	0x0,					
    0x44,	0x44,	0x44,	0x44,	0x44,	0x44,	0x0,	0x0,	0x0,			
    0x22,	0x17,	0x41,	0x0,	0x32,	0x36
    ]

    Gray4 = [										
    0x00,	0x60,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,			
    0x20,	0x60,	0x10,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,					
    0x28,	0x60,	0x14,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,					
    0x2A,	0x60,	0x15,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	 				
    0x00,	0x90,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	 				
    0x00,	0x02,	0x00,	0x05,	0x14,	0x00,	0x00,										
    0x1E,	0x1E,	0x00,	0x00,	0x00,	0x00,	0x01,									
    0x00,	0x02,	0x00,	0x05,	0x14,	0x00,	0x00,									
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,									
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,									
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,									
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,									
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,									
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,									
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,									
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,									
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,									
    0x24,	0x22,	0x22,	0x22,	0x23,	0x32,	0x00,	0x00,	0x00,							
    0x22,	0x17,	0x41,	0xAE,	0x32,	0x28,							
    ]	

    WF_FULL =	[			
    0x90,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,		
    0x60,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	
    0x90,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,		
    0x60,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,		
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,			
    0x19,	0x19,	0x00,	0x00,	0x00,	0x00,	0x00,		
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,			
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,		
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,				
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,					
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,					
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,			
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,		
    0x00,	0x00,	0x00,	0x00,	0x00,	0x00,	0x00,		
    0x24,	0x42,	0x22,	0x22,	0x23,	0x32,	0x00,	0x00,	0x00,		
    0x22,	0x17,	0x41,	0xAE,	0x32,	0x38
    ]

    def reset(self):
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(50) 
        epdconfig.digital_write(self.reset_pin, 0)
        epdconfig.delay_ms(2)
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(50)   

    def send_command(self, command):
        epdconfig.digital_write(self.dc_pin, 0)
        epdconfig.spi_writebyte([command])

    def send_data(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.spi_writebyte([data])

    def send_data2(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.spi_writebyte2(data)
        
    def ReadBusy(self, timeout=0.05):
        import time
        logger.debug("e-Paper busy")
        start = time.time()
        # 0: idle, 1: busy
        while epdconfig.digital_read(self.busy_pin) == 1:
            epdconfig.delay_ms(5) 
            if time.time() - start > timeout:
                logger.debug(f"e-Paper ReadBusy timeout ({timeout}s). Continuing...")
                break
        logger.debug("e-Paper busy release")  

    def TurnOnDisplay(self):
        self.send_command(0x22) # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0xc7)
        self.send_command(0x20) # MASTER_ACTIVATION
        self.ReadBusy(2.0)

    def TurnOnDisplay_Partial(self):
        self.send_command(0x22) # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0x0F)
        self.send_command(0x20) # MASTER_ACTIVATION
        self.ReadBusy(0.35)

    def lut(self, lut):
        self.send_command(0x32)
        for i in range(0, 153):
            self.send_data(lut[i])
        self.ReadBusy(0.05)

    def SetLut(self, lut):
        self.lut(lut)
        self.send_command(0x3f)
        self.send_data(lut[153])
        self.send_command(0x03)	# gate voltage
        self.send_data(lut[154])
        self.send_command(0x04)	# source voltage
        self.send_data(lut[155])	# VSH
        self.send_data(lut[156])	# VSH2
        self.send_data(lut[157])	# VSL
        self.send_command(0x2c)		# VCOM
        self.send_data(lut[158])

    def SetWindow(self, x_start, y_start, x_end, y_end):
        self.send_command(0x44) # SET_RAM_X_ADDRESS_START_END_POSITION
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data((x_start>>3) & 0xFF)
        self.send_data((x_end>>3) & 0xFF)
        self.send_command(0x45) # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data(y_end & 0xFF)
        self.send_data((y_end >> 8) & 0xFF)

    def SetCursor(self, x, y):
        self.send_command(0x4E) # SET_RAM_X_ADDRESS_COUNTER
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data(x & 0xFF)
        
        self.send_command(0x4F) # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)
        
    def init(self):
        if (epdconfig.module_init() != 0):
            return -1
        # EPD hardware init start     
        self.reset()

        self.ReadBusy()
        self.send_command(0x12)  #SWRESET
        self.ReadBusy() 

        self.send_command(0x01) #Driver output control      
        self.send_data(0x27)
        self.send_data(0x01)
        self.send_data(0x00)
    
        self.send_command(0x11) #data entry mode       
        self.send_data(0x03)

        self.SetWindow(0, 0, self.width-1, self.height-1)

        self.send_command(0x21) #  Display update control
        self.send_data(0x00)
        self.send_data(0x80)
    
        self.SetCursor(0, 0)
        self.ReadBusy()

        self.SetLut(self.WS_20_30)
        # EPD hardware init end
        return 0
    
    def init_Fast(self):
        if (epdconfig.module_init() != 0):
            return -1
        # EPD hardware init start     
        self.reset()

        self.ReadBusy()
        self.send_command(0x12)  #SWRESET
        self.ReadBusy() 

        self.send_command(0x01) #Driver output control      
        self.send_data(0x27)
        self.send_data(0x01)
        self.send_data(0x00)
    
        self.send_command(0x11) #data entry mode       
        self.send_data(0x03)

        self.SetWindow(0, 0, self.width-1, self.height-1)

        self.send_command(0x3C)   
        self.send_data(0x05)

        self.send_command(0x21) #  Display update control
        self.send_data(0x00)
        self.send_data(0x80)
    
        self.SetCursor(0, 0)
        self.ReadBusy()

        self.SetLut(self.WF_FULL)
        # EPD hardware init end
        return 0
    
    def Init_4Gray(self):
        if (epdconfig.module_init() != 0):
            return -1
        self.reset()
        epdconfig.delay_ms(100)

        self.ReadBusy()
        self.send_command(0x12)  #SWRESET
        self.ReadBusy() 

        self.send_command(0x01) #Driver output control      
        self.send_data(0x27)
        self.send_data(0x01)
        self.send_data(0x00)
    
        self.send_command(0x11) #data entry mode       
        self.send_data(0x03)

        self.SetWindow(8, 0, self.width, self.height-1)

        self.send_command(0x3C)
        self.send_data(0x04)
    
        self.SetCursor(1, 0)
        self.ReadBusy()

        self.SetLut(self.Gray4)
        # EPD hardware init end
        return 0

    def getbuffer(self, image):
        buf = [0xFF] * (int(self.width/8) * self.height)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        if(imwidth == self.width and imheight == self.height):
            logger.debug("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    if pixels[x, y] == 0:
                        buf[int((x + y * self.width) / 8)] &= ~(0x80 >> (x % 8))
        elif(imwidth == self.height and imheight == self.width):
            logger.debug("Horizontal")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if pixels[x, y] == 0:
                        buf[int((newx + newy*self.width) / 8)] &= ~(0x80 >> (y % 8))
        return buf
    
    def getbuffer_4Gray(self, image):
        buf = [0xFF] * (int(self.width / 4) * self.height)
        image_monocolor = image.convert('L')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        i=0
        if(imwidth == self.width and imheight == self.height):
            logger.debug("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    if(pixels[x, y] == 0xC0):
                        pixels[x, y] = 0x80
                    elif (pixels[x, y] == 0x80):
                        pixels[x, y] = 0x40
                    i= i+1
                    if(i%4 == 0):
                        buf[int((x + (y * self.width))/4)] = ((pixels[x-3, y]&0xc0) | (pixels[x-2, y]&0xc0)>>2 | (pixels[x-1, y]&0xc0)>>4 | (pixels[x, y]&0xc0)>>6)
                        
        elif(imwidth == self.height and imheight == self.width):
            logger.debug("Horizontal")
            for x in range(imwidth):
                for y in range(imheight):
                    newx = y
                    newy = self.height - x - 1
                    if(pixels[x, y] == 0xC0):
                        pixels[x, y] = 0x80
                    elif (pixels[x, y] == 0x80):
                        pixels[x, y] = 0x40
                    i= i+1
                    if(i%4 == 0):
                        buf[int((newx + (newy * self.width))/4)] = ((pixels[x, y-3]&0xc0) | (pixels[x, y-2]&0xc0)>>2 | (pixels[x, y-1]&0xc0)>>4 | (pixels[x, y]&0xc0)>>6) 
        return buf

    def display(self, image):
        if (image is None):
            return            
        self.send_command(0x24) # WRITE_RAM
        self.send_data2(image)   
        self.TurnOnDisplay()
        self._save_preview_if_mock(image)

    def display_Base(self, image):
        if (image is None):
            return   
            
        self.send_command(0x24) # WRITE_RAM
        self.send_data2(image)
                
        self.send_command(0x26) # WRITE_RAM
        self.send_data2(image)   
                
        self.TurnOnDisplay()
        self._save_preview_if_mock(image)

    def display_4Gray(self, image):
        self.send_command(0x24)
        for i in range(0, 4736):
            temp3=0
            for j in range(0, 2):
                temp1 = image[i*2+j]
                for k in range(0, 2):
                    temp2 = temp1&0xC0 
                    if(temp2 == 0xC0):
                        temp3 |= 0x00
                    elif(temp2 == 0x00):
                        temp3 |= 0x01  
                    elif(temp2 == 0x80): 
                        temp3 |= 0x01 
                    else: #0x40
                        temp3 |= 0x00 
                    temp3 <<= 1	
                    
                    temp1 <<= 2
                    temp2 = temp1&0xC0 
                    if(temp2 == 0xC0): 
                        temp3 |= 0x00
                    elif(temp2 == 0x00): 
                        temp3 |= 0x01
                    elif(temp2 == 0x80):
                        temp3 |= 0x01
                    else :   #0x40
                        temp3 |= 0x00	
                    if(j!=1 or k!=1):				
                        temp3 <<= 1
                    temp1 <<= 2
            self.send_data(temp3)
            
        self.send_command(0x26)	       
        for i in range(0, 4736):
            temp3=0
            for j in range(0, 2):
                temp1 = image[i*2+j]
                for k in range(0, 2):
                    temp2 = temp1&0xC0 
                    if(temp2 == 0xC0):
                        temp3 |= 0x00
                    elif(temp2 == 0x00):
                        temp3 |= 0x01
                    elif(temp2 == 0x80):
                        temp3 |= 0x00
                    else: #0x40
                        temp3 |= 0x01 
                    temp3 <<= 1	
                    
                    temp1 <<= 2
                    temp2 = temp1&0xC0 
                    if(temp2 == 0xC0): 
                        temp3 |= 0x00
                    elif(temp2 == 0x00): 
                        temp3 |= 0x01
                    elif(temp2 == 0x80):
                        temp3 |= 0x00 
                    else:    #0x40
                        temp3 |= 0x01	
                    if(j!=1 or k!=1):					
                        temp3 <<= 1
                    temp1 <<= 2
            self.send_data(temp3)

        self.TurnOnDisplay()
        # Preview for 4Gray is not fully mapped here but we log it
        logger.info("4Gray image displayed (preview not supported)")
        
    def display_Partial(self, image, previous_image=None):
        if (image is None):
            return
            
        epdconfig.digital_write(self.reset_pin, 0)
        epdconfig.delay_ms(2)
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(2)   
        
        self.SetLut(self.WF_PARTIAL_2IN9)
        self.send_command(0x37)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x40)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)  
        self.send_data(0x00)

        self.send_command(0x3C) #BorderWavefrom
        self.send_data(0x80)

        self.send_command(0x22) 
        self.send_data(0xC0)
        self.send_command(0x20)
        self.ReadBusy()

        # 1. Write the new image to 0x24 RAM
        self.SetWindow(0, 0, self.width - 1, self.height - 1)
        self.SetCursor(0, 0)
        self.send_command(0x24) # WRITE_RAM
        self.send_data2(image)   

        # 2. Write the previous image to 0x26 RAM (Old RAM) if provided.
        # This is critical when waking from deep sleep so the controller knows what pixels to clear.
        if previous_image is not None:
            self.SetWindow(0, 0, self.width - 1, self.height - 1)
            self.SetCursor(0, 0)
            self.send_command(0x26) # WRITE_RAM_RED
            self.send_data2(previous_image)
            
        self.TurnOnDisplay_Partial()
        self._save_preview_if_mock(image)

    def Clear(self, color=0xFF):
        if self.width%8 == 0:
            linewidth = int(self.width/8)
        else:
            linewidth = int(self.width/8) + 1

        self.send_command(0x24) # WRITE_RAM
        self.send_data2([color] * int(self.height * linewidth)) 
        self.TurnOnDisplay()
        self.send_command(0x26) # WRITE_RAM
        self.send_data2([color] * int(self.height * linewidth)) 
        self.TurnOnDisplay()

        # Save blank preview if in mock mode
        self._save_preview_if_mock([color] * int(self.height * linewidth))

    def sleep(self):
        self.send_command(0x10) # DEEP_SLEEP_MODE
        self.send_data(0x01)
        
        epdconfig.delay_ms(100)
        epdconfig.module_exit()

    def _save_preview_if_mock(self, image_buffer):
        # Safely determine mock status
        is_mock = getattr(epdconfig, "MOCK_MODE", False) or getattr(epdconfig, "mock_mode", False) or (hasattr(epdconfig, "implementation") and getattr(epdconfig.implementation, "mock_mode", False))
        if is_mock:
            try:
                from PIL import Image
                # Reconstruct image from vertical buffer (128x296)
                img = Image.frombytes('1', (self.width, self.height), bytes(image_buffer))
                
                # To get back the horizontal 296x128 representation:
                # The getbuffer() maps:
                # newx = y
                # newy = self.height - x - 1
                # This is a rotation. Let's rotate 270 degrees and mirror or transpose to restore it.
                # Actually, Transpose works perfectly:
                # Since getbuffer horizontal path is:
                #   newx = y
                #   newy = height - x - 1
                # Reverting this mathematically:
                #   x = height - newy - 1
                #   y = newx
                # This corresponds to rotating the 128x296 image by 270 degrees (clockwise 270, i.e. 90 counter-clockwise).
                # Let's rotate 90 degrees CCW:
                img_rotated = img.rotate(90, expand=True)
                
                # Save to preview path
                preview_path = "/tmp/ink_screen_preview.png"
                img_rotated.save(preview_path)
                logger.info(f"Mock preview image successfully written to {preview_path}")
            except Exception as e:
                logger.error(f"Error generating mock preview image: {e}")
