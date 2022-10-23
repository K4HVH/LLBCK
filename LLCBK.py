from queue import Queue
import time
import argparse
from xml.etree.ElementTree import TreeBuilder
from rpi_ws281x import PixelStrip, Color
import PySimpleGUI as sg
import multiprocessing as mp
import sys
import itertools as it

def LLCBK_window():
    sg.theme("DarkBrown4")

    basic_layout = [
        [sg.Button("Classic", size=(12, 4), font='PibotoLt 30'), sg.Text("Select\nLight\nStyle", size=(6, None), font='PibotoLt 30', justification="center"), sg.Button("Animated", size=(12, 4), font='PibotoLt 30')],
        [sg.Button("Lightshow", size=(12, 4), font='PibotoLt 30'), sg.Button("Off", size=(5, 4), font='PibotoLt 30'), sg.Button("Advanced Mode", size=(12, 4), font='PibotoLt 30')]
    ]

    advanced_layout = [
        [sg.Button("Simple Mode"), sg.Button("Shut Down")]
    ]

    layout = [[sg.Column(basic_layout, key="-Simple Mode-"), sg.Column(advanced_layout, visible=False, key="-Advanced Mode-")]]

    window = sg.Window("LLCBK", layout, size=(800,480), element_justification="center", finalize=True)
    window.Maximize()
    return window

def guiMain():
    window = LLCBK_window()

    while True:
        event, values = window.read()

        if event != (sg.WIN_CLOSED):
            print('============ Event = ', event, ' ==============')
            print('-------- Values Dictionary (key=value) --------')
            for key in values:
                print(key, ' = ',values[key])
        
        if event in (sg.WIN_CLOSED, "Shut Down"):
            print("[LOG] Clicked Shutdown")
            break

        if event == ("Off"):
            print("[LOG] Clicked Off")
        elif event == ("Classic"):
            print("[LOG] Clicked Classic")
        elif event == ("Animated"):
            print("[LOG] Clicked Animated")
        elif event == ("Lightshow"):
            print("[LOG] Clicked Lightshow")
        elif event == ("Advanced Mode"):
            print("[LOG] Clicked Advanced Mode")
            window[f'-Simple Mode-'].update(visible=False) # This is done so poorly I know
            window[f'-Advanced Mode-'].update(visible=True) # If I need to expand in future I may do it properly
        elif event == ("Simple Mode"):
            print("[LOG] Clicked Simple Mode")
            window[f'-Advanced Mode-'].update(visible=False)
            window[f'-Simple Mode-'].update(visible=True)

    raise RuntimeError("Gui Shutdown")
    window.close()
    sys.exit()



#######################################################
#Everythign above here is GUI stuff

#Controlling definitions of the strips. All of them have to be sequential because only
#GPIO 18 and 21 support the type of PWM output we want.
#So either we have all rear lights on 1 header, and all front on the other (This hasnt
#been tested for performance yet, thats ~1000 leds on the rear :/

#Available GPIO pins and respective channels
#    PIN   |   Channel
#     18   |      0
#     12   |      0
#     21   |      0     
#     13   |      1
#     19   |      1

# Rear strip configuration:
RS_COUNT = 965       # Number of LED pixels.
RS_PIN = 18          # GPIO pin connected to the pixels
RS_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
RS_DMA = 10          # DMA channel to use for generating signal (try 10)
RS_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
RS_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
RS_CHANNEL = 0       # Reserving CH 1 for Front LEDS

# Front strip configuration:
FS_COUNT = 120       # Number of LED pixels.
FS_PIN = 13          # GPIO pin connected to the pixels
FS_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
FS_DMA = 10          # DMA channel to use for generating signal (try 10)
FS_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
FS_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
FS_CHANNEL = 1       # Reserving CH 0 for Rear LEDS

# Ok here we figure out the size and ring dimensions for our animations to use
# At some stage we will also have to figure out delays for multi-ring wipes but that
# is going to be a bitch so it will come later

# Large Ring (Main Size (172mm))
RR_TOTALRINGS = 9
RR_TOTALLEDS = 241
RR_INDILEDCOUNT = [60, 48, 40, 32, 24, 16, 12, 8, 1]
RR_RINGSTARTLED = [0, 60, 108, 148, 180, 204, 220, 232, 240, 241]
RR_RINGENDLED = [60, 108, 148, 180, 204, 220, 232, 240, 241, 242]

MR_TOTALRINGS = 9
MR_TOTALLEDS = 241
MR_INDILEDCOUNT = [60, 48, 40, 32, 24, 16, 12, 8, 1]
MR_RINGSTARTLED = [241, 301, 349, 389, 421, 445, 461, 473, 481, 482]
MR_RINGENDLED = [301, 349, 389, 421, 445, 461, 473, 481, 482, 483]

ML_TOTALRINGS = 9
ML_TOTALLEDS = 241
ML_INDILEDCOUNT = [60, 48, 40, 32, 24, 16, 12, 8, 1]
ML_RINGSTARTLED = [482, 542, 590, 630, 662, 686, 702, 714, 722, 723]
ML_RINGENDLED = [542, 590, 630, 662, 686, 702, 714, 722, 723, 724]

RL_TOTALRINGS = 9
RL_TOTALLEDS = 241
RL_INDILEDCOUNT = [60, 48, 40, 32, 24, 16, 12, 8, 1]
RL_RINGSTARTLED = [723, 783, 831, 871, 903, 927, 943, 955, 963, 964]
RL_RINGENDLED = [783, 831, 871, 903, 927, 943, 955, 963, 964, 965]

def LEDS_ALL(r1start, r1stop, r2start, r2stop, r3start, r3stop, r4start, r4stop, step=1):
    return it.chain(range(RR_RINGSTARTLED[r1start], RR_RINGENDLED[r1stop], step), range(MR_RINGSTARTLED[r2start], MR_RINGENDLED[r2stop], step), range(ML_RINGSTARTLED[r3start], ML_RINGENDLED[r3stop], step), range(RL_RINGSTARTLED[r4start], RL_RINGENDLED[r4stop], step))

def LEDS_RIGHT(r1start, r1stop, r2start, r2stop, step=1):
    return it.chain(range(RR_RINGSTARTLED[r1start], RR_RINGENDLED[r1stop], step), range(MR_RINGSTARTLED[r2start], MR_RINGENDLED[r2stop], step))

def LEDS_LEFT(r3start, r3stop, r4start, r4stop, step=1):
    return it.chain(range(ML_RINGSTARTLED[r3start], ML_RINGENDLED[r3stop], step), range(RL_RINGSTARTLED[r4start], RL_RINGENDLED[r4stop], step))

def LEDS_OUT(r1start, r1stop, r4start, r4stop, step=1):
    return it.chain(range(RR_RINGSTARTLED[r1start], RR_RINGENDLED[r1stop], step), range(RL_RINGSTARTLED[r4start], RL_RINGENDLED[r4stop], step))

def LEDS_IN(r2start, r2stop, r3start, r3stop, step=1):
    return it.chain(range(MR_RINGSTARTLED[r2start], MR_RINGENDLED[r2stop], step), range(ML_RINGSTARTLED[r3start], ML_RINGENDLED[r3stop], step))

def LEDS_RR(r1start, r1stop, step=1):
    return it.chain(range(RR_RINGSTARTLED[r1start], RR_RINGENDLED[r1stop], step)) 

def LEDS_MR(r2start, r2stop, step=1):
    return it.chain(range(MR_RINGSTARTLED[r2start], MR_RINGENDLED[r2stop], step))

def LEDS_ML(r3start, r3stop, step=1):
    return it.chain(range(ML_RINGSTARTLED[r3start], ML_RINGENDLED[r3stop], step))

def LEDS_RL(r4start, r4stop, step=1):
    return it.chain(range(RL_RINGSTARTLED[r4start], RL_RINGENDLED[r4stop], step))

# This shit above is so cancer but its pretty much the only way this will work 
# in a compact fashion because python is aids. Why the fuck do people use this
# lang over C++ it fucking baffles me

# Heres the plan on how do do everything to start off with
# Writing this down so I can make changes and so that I dont forget cause I am
# a moron

# For modes of operation, it wont actually matter whether the lights are on or not, 
# this is because they are just going to operate the same way during the day too

# Light States
# 1.) No Condition
#   1.5) Indicating 
# 2.) Brake Down
#   2.5) Indicating
# 3.) Maybe Brake Up *******
#   3.5) Indicating  *******
# 4.) Reversing
#   4.5) Indicating




def Mode1(strip):

    # Clear the interior LEDs from any residual animation or whatever
    for i in LEDS_ALL(2, 8, 2, 8, 2, 8, 2, 8):
        strip.setPixelColor(i, Color(0, 0, 0))
    #strip.show() 

    # Make sure the LEDs we are changing are part of our strip
    for j in range(10): 
        # Set the First Ring
        for i in LEDS_ALL(0, 0, 0, 0, 0, 0, 0, 0):
            strip.setPixelColor(i, Color(255, 0, 0))
        for q in range(6): 
            for i in LEDS_LEFT(1, 1, 1, 1, 6):
                strip.setPixelColor(i + q, Color(255, 0, 0))
            for i in LEDS_RIGHT(1, 1, 1, 1, 6):
                strip.setPixelColor(i - q + 5, Color(255, 0, 0))
            strip.show() # We Commit here for the animation
            time.sleep(25/1000)
            for i in LEDS_LEFT(1, 1, 1, 1, 6):
                strip.setPixelColor(i + q, Color(0, 0, 0))
            for i in LEDS_RIGHT(1, 1, 1, 1, 6):
                strip.setPixelColor(i - q + 5, Color(0, 0, 0))

def Mode15(strip, side):

    # Clear the interior LEDs from any residual animation or whatever
    for i in LEDS_ALL(2, 8, 2, 8, 2, 8, 2, 8):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

    if side == 0:  #Turning Right
        # Make sure the LEDs we are changing are part of our strip
        for j in range(10):
            # Set the First Ring
            for i in LEDS_ALL(0, 0, 0, 0, 0, 0, 0, 0):
                strip.setPixelColor(i, Color(255, 0, 0))
            
            for q in range(6): 
                for i in LEDS_ALL(1, 1, 1, 1, 1, 1, 1, 1, 6):
                    strip.setPixelColor(i + q, Color(255, 0, 0))
                strip.show() # We Commit here for the animation
                time.sleep(25/1000)
                for i in LEDS_ALL(1, 1, 1, 1, 1, 1, 1, 1, 6):
                    strip.setPixelColor(i + q, Color(0, 0, 0))

    elif side == 2:
        print("Here")




def Mode2(strip):
    # Make sure the LEDs we are changing are part of our strip
    for j in range(2):
        # Set the First Ring
        for i in LEDS_ALL(0, 0, 0, 0, 0, 0, 0, 0):
            strip.setPixelColor(i, Color(255, 0, 0))
        strip.show() # We Commit here for the animation
        time.sleep(40/1000)
        for i in LEDS_ALL(1, 1, 1, 1, 1, 1, 1, 1):
            strip.setPixelColor(i, Color(255, 0, 0))
        strip.show() # We Commit here for the animation
        time.sleep(40/1000)
        for i in LEDS_ALL(2, 2, 2, 2, 2, 2, 2, 2):
            strip.setPixelColor(i, Color(255, 0, 0))
        strip.show() # We Commit here for the animation
        time.sleep(40/1000)
        for i in LEDS_ALL(3, 3, 3, 3, 3, 3, 3, 3):
            strip.setPixelColor(i, Color(255, 0, 0))
        strip.show() # We Commit here for the animation
        time.sleep(40/1000)
        for i in LEDS_ALL(4, 4, 4, 4, 4, 4, 4, 4):
            strip.setPixelColor(i, Color(255, 0, 0))
        strip.show() # We Commit here for the animation
        time.sleep(40/1000)
        for i in LEDS_ALL(5, 5, 5, 5, 5, 5, 5, 5):
            strip.setPixelColor(i, Color(255, 0, 0))

def rsMain():
    strip = PixelStrip(RS_COUNT, RS_PIN, RS_FREQ_HZ, RS_DMA, RS_INVERT, RS_BRIGHTNESS, RS_CHANNEL) 
    strip.begin()
    # This is just gives the data to the strips then tells them to get ready

    # Here we actually control the LEDs
    # This will probably get put into its own function once I have all the rings
    # and there respective functions made up

    while True:
        
        pM1 = mp.Process(target=Mode1, args=(strip, ))
        #pIndi = mp.Process(target=Mode15, args=(strip, 0))
        #pM2 = mp.Process(target=Mode2, args=(strip, ))

        pM1.start()
        pM1.join()
        #pM1.kill()

        #pM2.start()
        #pM2.join()
        #pM2.kill()

        #pIndi.start()
        #pIndi.join()
        #pIndi.kill()
    else:
        colorWipe(strip, Color(0, 0, 0), 10)


def fsMain():
    strip = PixelStrip(FS_COUNT, FS_PIN, FS_FREQ_HZ, FS_DMA, FS_INVERT, FS_BRIGHTNESS, FS_CHANNEL) 
    strip.begin()
    # This is just gives the data to the strips then tells them to get ready

    # Here we actually control the LEDs
    # This will probably get put into its own function once I have all the rings
    # and there respective functions made up
    #while True:
        #colorWipe(strip, Color(0, 0, 255))  # Blue wipe
        #colorWipe(strip, Color(255, 0, 0))  # Red wipe
        #colorWipe(strip, Color(0, 255, 0))  # Green wipe
    #else:
        #colorWipe(strip, Color(0, 0, 0), 10)

# This is where everything actually runs, we only want to call the functions of drawing
# the menu aswell as the front and rear strip main functions to simplify call structure
# We utilise multiprocessing so that the GUI and both strips can run synchronously
# However, this makes catching the exception to close the program a real pain because
# the different threads wont tell each other about the exception, so, to deal with this
# we just assume that if we ever get to a exit point in the menu code, and that PID
# stops, then we should just shut down the strip functions too
if __name__ == "__main__":

    p1 = mp.Process(target=guiMain,)
    p2 = mp.Process(target=rsMain, args=())
    p3 = mp.Process(target=fsMain, args=())

    p1.start()
    p2.start()
    p3.start()

    p2.kill()

    p4 = mp.Process(target=rsMain)
    p4.start()

    p1.join()
    # The only way we ever get paste here is if the menu shuts down, so we can safely
    # assume that we should just kill whatever processes are left

    p3.kill()
    p4.kill()


    
 