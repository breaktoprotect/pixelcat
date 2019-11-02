#!/usr/bin/python
'''
Version     : v0.1
Author      : Jeremy S. @breaktoprotect
Description : Transfer data from display via encoded-decoded pixels
Supported Python: Python 2.7.15rc1 (may work on other Python 2.7)
'''
import argparse
import sys
import numpy
import scipy.misc as smp
from PIL import Image, ImageTk
import Tkinter as tk
import binascii
import time
import pyautogui
import random
import os
import glob

from pixelcat_util import * #pixelcat imports

### App notes setup ###
APP_VERSION = "v0.1"

### Argparse setup ###
parser = argparse.ArgumentParser(description='pixelcat ' + APP_VERSION)

parser.add_argument('-l', action='store_true', default=False, dest='LISTEN', help='Set tool to LISTENING mode to screen capture encoded pixel images.')
parser.add_argument('-i', action='store',dest='FILENAME',help='Specify the input file to transfer.')
parser.add_argument('-ac', action='store_true',default=False, dest='ANTI_COMPRESSION', help='Turn on anti-compression mode. Slower transfer.')
parser.add_argument('--debug', action='store_true',default=False, dest='DEBUG', help='Run debugPrintToScreen() function.')
parser.add_argument('--custom', action='store_true',default=False,dest='CUSTOM', help='Run custom debug codes.')
parser.add_argument('--diag', action='store_true',default=False,dest='DIAG', help='Run diagnostics.')
parser.add_argument('--version', action='version', version='pixelcat ' + APP_VERSION)

### Detect screen resolution ###
root = tk.Tk()
width = root.winfo_screenwidth()
height = root.winfo_screenheight()
print "width:", width
print "height:", height
root.withdraw()
root.after(500, root.destroy) #0.5sec lag
root.mainloop()

### Notch or borders compensation ###
COMP_Y = 32
COMP_X = 0

### Extremes ###
X1 = 0 + COMP_X #absolute first usable pixel at X axis
Y1 = 0 + COMP_Y #absolute first usable pixel at Y axis
BANDWIDTH_COMP = 0 # 0 is no decrease; 500 means reduced screen real estate by 500 Y pixels
X2 = width - 1 #absolute last usable pixel at X axis
Y2 = (height - BANDWIDTH_COMP) - 1  #absolute last usable pixel at Y axis
#X2 = width -1
#Y2 = height - 1

### Other essential constants ###
CAPTURE_INTERVAL = 2    # in secs (should be >= to SPLASH PERIOD; stability issues over high latency)
SPLASH_PERIOD = 2       # in secs

'''**************************** TRANSMITTER ****************************'''
'''*********************************************************************'''

''' Test bench ''' #To be removed later
def customDebug():
    pixels = imageToPixel("test-samples/out-vdi-sample.png")
    print("Magic headers: "),
    print pixels[2,2],
    print pixels[2,3]
    
    print ("2,11: "),
    print pixels[2,11]

    pixels2 = imageToPixel("test-samples/in-vdi sample.png")
    print("Magic headers: "),
    print pixels2[2,2],
    print pixels2[2,3]
    print ("2,11: "),
    print pixels2[2,11]

    pass

def diagnostics():
    pixels = numpy.zeros( (height,width, 3), dtype=numpy.uint8 )
    
    # Starting from pixel[1,0]
    # R, G and B region 0 to 64
    for x in range(0,63):
        for y in range(0,63):
            for z in range(0,63):
                pixels[1+x,1+y+z] = [x,y,z]
    
    # Starting from pixel[100,0]
    for x in range(0,127):
        for y in range(0,127):
            for z in range(0,127):
                pixels[100+x,1+y+z] = [x,y,z]

    # Starting from pixel[300,0]
    for x in range(0,255):
        for y in range(0,255):
            for z in range(0,255):
                pixels[300+x,1+y+z] = [x,y,z]
    splash(pixels)
    pass

def debugPrintToScreen():
    ### Create based on current resolution (e.g. 1080p = 1920 x 1080)
    ### array of 8 bit unsigned integers
    data = numpy.zeros( (height,width, 3), dtype=numpy.uint8 )

    #debug coloring  
    #top left (start)
    data[Y1, X1] = [0,255,0]

    #bottom right (end)
    data[Y2, X2] = [123,123,123]

    #encoding "header" markers
    data[2,2] = (100,101,102)
    data[2,3] = (200,201,202)

    #random
    for x in range(100):
        data[50,x] = [100,100,100]

    #debug
    print("Screen width: %d" % width)
    print("Screen height: %d" % height)

    #img = smp.toimage( data )       # Create a PIL image
    #img.show()                      # View in default viewer

    #debug
    #img.save('save.png')

    ### Splash Screen ###
    
    splash(data)

def splash(pixelData):
    root = tk.Tk()
    ### Screen Setup ###
    root.geometry('%dx%d+%d+%d' % (width, height, 0, 0))
    root.wm_attributes('-fullscreen', True)
    root.overrideredirect(True)
    root.config(cursor="none") #disable the mouse cursor when displaying
    root.overrideredirect(1) #remove border

    ### Pixel to Tkinter Image conversion ###
    img = Image.fromarray(pixelData)
    imgTk = ImageTk.PhotoImage(img)
    canvas = tk.Canvas(root, height=height+2, width=width+2, bg="green", highlightthickness=0, bd=0) # bd: border size
    canvas.create_image((width/2), (height/2), image=imgTk) #960 and 540 is just halved the respective x and y
    canvas.pack()

    # show the splash screen for n milliscmdeconds then destroy
    root.after(int(SPLASH_PERIOD * 1000), root.destroy)
    root.mainloop()

''' @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ '''
''' Anti-Compression: Black and white Binary encoding '''
''' @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ '''
def ac_encoder(inputFile):
    ### Read file ###
    f = open(inputFile, "rb").read()
    
    ### Convert to binary representation 0 and 1 ###
    hexadecimal = bin(int(binascii.hexlify(f),16))
    binList = hexadecimal[2:]
    binListLength = len(binList)
    
    #debug
    #print("Binary represented: %s", binList)

    ### Convert OrdList into Numpy Array Pixel style ###
    pixels = numpy.zeros( (height,width, 3), dtype=numpy.uint8 )
    ptrX = 0+COMP_X
    ptrY = 0+COMP_Y
    ptrPage = 0

    ### Set the signature/magic header
    pixels = ac_setMagicHeader(pixels)

    ### Set the binary length to the header
    pixels = ac_setLength(binListLength, pixels)

    for cursor in xrange(0,binListLength):
        if binList[cursor] == '1':
            pixels[ptrY, ptrX] = (255,255,255)
        else:
            pixels[ptrY, ptrX] = (0,0,0)

        # Shift to next pixel
        ptrX += 1

        #Check X and Y coordinates if there is any spill over
        if ptrX == X2:
            ptrY += 1
            ptrX = 0

        if ptrY == Y2:
            #debug
            print("End of page! Current Page Number is %d" % ptrPage)
            splash(pixels)

            ### Setting a delay - test in progress ###
            time.sleep(CAPTURE_INTERVAL)

            ### Save to file TODO:temp only
            #encodedData = smp.toimage(pixels)
            #encodedData.save(inputFile +"_%d.png" % ptrPage)
            
            ### Reset Pixels and various pointers ###
            ptrPage += 1
            pixels = numpy.zeros((height, width, 3), dtype=numpy.uint8)
            ptrX = 0+COMP_X
            ptrY = 0+COMP_Y       

            ### Set the signature/magic header
            pixels = ac_setMagicHeader(pixels)

            ### Set the binary length to the header
            pixels = ac_setLength(binListLength, pixels)

            # Update page number on pixel Image
            pixels = ac_setPageNumber(ptrPage,pixels)
      
            continue

    #debug
    print("bin length: ", len(binList))
    print(pixels[COMP_Y, COMP_X])

    ### Set the last page header
    pixels = ac_setLastPage(pixels)

    ### Set filename on the last page
    pixels = ac_setFilename(inputFile, pixels)

    splash(pixels)

'''def ac_decoder():
    pass'''
''' -------------------------------- '''
''' Standard hex to RGB ord encoding '''
''' -------------------------------- '''
def encoder(inputFile):
    ### Read file ###
    f = open(inputFile, "rb").read()
    fHex = f.encode("hex")

    ### Looping through the hex and converting into ascii ordinal array
    ptr = 0
    ordList = []

    for _ in range(len(fHex)/2):
        bufferStr = fHex[ptr:(ptr+2)]
        ptr += 2
        ordList.append(int(bufferStr,16)) 


    #debug: print out the ordList info
    print "Size of ordList: %d" % len(ordList)
    print "Pixels required: %d" % (len(ordList)/3)

    ### Convert OrdList into Numpy Array Pixel style ###
    pixels = numpy.zeros( (height,width, 3), dtype=numpy.uint8 )
    ptrX = 0+COMP_X
    ptrY = 0+COMP_Y
    ptrPage = 0

    #debug: copy from debugPrintToScreen() corners:
    #pixels[Y1, X1] = [0,255,0] #top left (start) 
    #pixels[Y2, X2] = [123,123,123] #bottom right (end)

    ### Mark "header" pixels for identification (Sig, length of pixels, page)
    ### Pixel order: Sig (2pixels), Length of pixel array (2pixels), Page (1 pixel)
    # Header # [pixel1][pixel2]
    pixels[2,2] = (100,101,102)
    pixels[2,3] = (200,201,202)

    # Length of Pixel Array [pixel][pixel] - Hex format in integer, left (255) is largest, right (255) is smallest. (E.g. pixel_length = 3000, then it is (0,0,0),(0,11,184)
    # Variables position: (n5,n4,n3)(n2,n1,n0)
    pixLength = len(ordList)/3
    n = intToPixel(pixLength, 2) #require 2 pixels
        
    # Setting the pixel size into pixel representation
    pixels[2,4][0] = n[5]
    pixels[2,4][1] = n[4]
    pixels[2,4][2] = n[3]
    pixels[2,5][0] = n[2]
    pixels[2,5][1] = n[1]
    pixels[2,5][2] = n[0]

    ### pixels[2,10] - 1 pixel only - is reserved for page numbers (0,0,0) Most Right is LSB
    ### e.g. page 260 is (0,1,4)
    ptrPage = 0 

    # Update page number on pixel Image
    pixelPageNum = intToPixel(ptrPage,1)
    pixels[2,10][0] = pixelPageNum[2]
    pixels[2,10][1] = pixelPageNum[1]
    pixels[2,10][2] = pixelPageNum[0]     

    for cursor in xrange(0,len(ordList),3):
        #debug
        #print("Processing: %d" % ordList[x]) 
        
        ### Check if less than 3 ordinals left on the list
        leftover = len(ordList) - cursor
        if leftover <= 0:
            pixels[2,11] = [011,111,110] #mark pixel to be last page
            break
        elif leftover == 2:
            pixels[ptrY,ptrX] = [ordList[cursor],ordList[cursor+1],0]
            pixels[2,11] = [011,111,110] #mark pixel to be last page
            break
        elif leftover == 1:
            pixels[ptrY,ptrX] = [ordList[cursor],0,0]
            pixels[2,11] = [011,111,110] #mark pixel to be last page
            break
        else:
            #Encoding bytes into pixels
            pixels[ptrY,ptrX] = [ordList[cursor], ordList[cursor+1], ordList[cursor+2]]
             
            ptrX += 1

            ### Check for last page
            try:
                testVar = ordList[cursor+3]
                
            except:
                #debug
                print("encoder(): last page check reached!")
                pixels[2,11] = [011,111,110] #mark pixel to be last page



            #Check X and Y coordinates if there is any spill over
            if ptrX == X2:
                ptrY += 1
                ptrX = 0

            if ptrY == Y2:
                #debug
                print("End of page! Current Page Number is %d" % ptrPage)
                splash(pixels)

                ### Save to file TODO:temp only
                #encodedData = smp.toimage(pixels)
                #encodedData.save(inputFile +"_%d.png" % ptrPage)
                
                ### Reset Pixels and various pointers ###
                ptrPage += 1
                pixels = numpy.zeros((height, width, 3), dtype=numpy.uint8)
                ptrX = 0+COMP_X
                ptrY = 0+COMP_Y       
                pixels[2,2] = (100,101,102) #pixelcat headers
                pixels[2,3] = (200,201,202) #

                # Update page number on pixel Image
                pixelPageNum = intToPixel(ptrPage,1)
                pixels[2,10][0] = pixelPageNum[2]
                pixels[2,10][1] = pixelPageNum[1]
                pixels[2,10][2] = pixelPageNum[0]         
                continue

    splash(pixels)
    #encodedData = smp.toimage(pixels)
    #encodedData.save(inputFile +"_%d.png" % ptrPage)
    
'''***************************** LISTENER ******************************'''
'''*********************************************************************'''
def captureScreen():
    # Generate a hash filename as a temporary buffer
    hashID = str(random.getrandbits(64))
    print("[*] Pixelcat has started listening. Mode: Standard")
    print("[*] hashID: " + hashID)

    while (True):
        img = pyautogui.screenshot()
        screenPixels = numpy.asarray(img)
        pageNumber = -1
        #img.show()
        #screenPixels = imageToPixel("manual.png")

        ### Detect Headers & Validate ###
        try:
            if screenPixels[2,2][0] == 100 and screenPixels[2,2][1] == 101 and screenPixels[2,2][2] == 102 and screenPixels[2,3][0] == 200 and screenPixels[2,3][1] == 201 and screenPixels[2,3][2] == 202:
                #TODO:
                #debug
                print("captureScreen() Detected valid pixelcat headers!")
                print("Page number: " + str(pixelToInt(screenPixels[2,10])))
                encodedData = smp.toimage(screenPixels)
                pageNumber = pixelToInt(screenPixels[2,10])
                encodedData.save(hashID + "_%d.png" % pageNumber) #with Pg number

        except Exception as exception:
            print str(exception)
            continue

        ### Condition to stop loop: Pixel[2,11] must contain (011, 111, 110)
        ### A "last-page" flag set by encoder
        if numpy.all(screenPixels[2,11] == [011,111,110]): 
            print("[*] BREAK! Found end page flag [011,111,110]")
            break

        time.sleep(CAPTURE_INTERVAL)

    print("[+] Capture completed.")

    ### Start decoding in sequence ###    
    print("[*] Decoding in progress...Please wait.")
    decoder(hashID)    
    print("[+] Decoding completed! File is saved as: decoded_" + hashID)

    ### Clean up
    #cleanUpTempFiles(hashID)

def ac_captureScreen():
    # Generate a hash filename as a temporary buffer
    hashID = "ac" + str(random.getrandbits(64))
    print("[*] Pixelcat has started listening. Mode: Anti-Compression")
    print("[*] hashID: " + hashID)

    while (True):
        img = pyautogui.screenshot()
        screenPixels = numpy.asarray(img)
        pageNumber = -1 #init only

        #debug
        '''img.show()
        #screenPixels = imageToPixel("manual.png")
        '''

        if ac_detectMagicHeader(screenPixels):
            encodedData = smp.toimage(screenPixels)
            pageNumber = ac_getPageNumber(screenPixels)
            encodedData.save(hashID + "_%d.png" % pageNumber)


        ### Detect Headers & Validate ###
        #TODO 
        '''
        try:
            if screenPixels[2,2][0] == 100 and screenPixels[2,2][1] == 101 and screenPixels[2,2][2] == 102 and screenPixels[2,3][0] == 200 and screenPixels[2,3][1] == 201 and screenPixels[2,3][2] == 202:
                #TODO:
                #debug
                print("captureScreen() Detected valid pixelcat headers!")
                print("Page number: " + str(pixelToInt(screenPixels[2,10])))
                encodedData = smp.toimage(screenPixels)
                pageNumber = pixelToInt(screenPixels[2,10])
                encodedData.save(hashID + "_%d.png" % pageNumber) #with Pg number

        except Exception as exception:
            print str(exception)
            continue
        '''

        ### Condition to stop loop: Pixel[2,11] must contain (011, 111, 110)
        ### A "last-page" flag set by encoder

        #temp break
        #TODO
        if ac_detectLastPage(screenPixels) is True:
            print("[*] BREAK! Found last page header found with 0101010101 tag")
            break
        '''
        if numpy.array_equal(screenPixels[2,11], (123,123,123)):
            print("[*] BREAK! Found end page flag [123,123,123]")
            break
        '''
        #Turning it off temporarily to see if it's even needed
        #time.sleep(CAPTURE_INTERVAL)

    ### Start decoding in sequence ###    
    print("[+] Capture completed.")
    print("[*] Decoding in progress...Please wait.")
    ac_decoder(hashID)    
    print("[+] Decoding completed! File is saved as: decoded_" + hashID)

    ### Clean up 
    #Moved to later stage    

def ac_decoder(hashID):
    ptrPage = 0         # Current encodedFile page
    pixels = imageToPixel(hashID + "_%d.png" % ptrPage)
    ptrX = 0+COMP_X     # Starting position
    ptrY = 0+COMP_Y     # Starting position   
    binList = []

    ### Check header, pixel length, and page number
    # Header @ pixels[2,2] = (100,101,102); pixels[2,3] = (200,201,202)
    #TODO
    #may not be necessary
 
    pixelLength = ac_getLength(pixels)
    pageNum = ac_getPageNumber(pixels)

    ### Pack pixels data into a binList[] ###
    for _ in range(pixelLength):
        ### Verify if page is in sequence 
        ### TODO: need to check if necessary
        if ptrPage != pageNum:
            print("decoder() error: Page is not decoded in sequence!")
            
            #debug
            print("decoder() ptrPage: %d" % ptrPage)
            print("decoder() pageNum: %d" % pageNum)

            sys.exit(1)

        ### Extraction with error correction
        binList.append( ac_estimatePixelStr(pixels[ptrY,ptrX]) )

        """ old without error correction
        ### Extracting  (binary)
        if numpy.array_equal(pixels[ptrY,ptrX], (0,0,0)):
        #if (pixels[ptrY,ptrX] == (0,0,0)).all():
            binList.append('0')
        else:
            binList.append('1')
        """

        ### Progress and Adjust Pointers ###
        ptrX += 1

        #Check and adjust X and Y coordinates if there is any spill over
        if ptrX == X2:
            ptrY += 1
            ptrX = 0
    
        if ptrY == Y2:
            #TODO
            print("decoder() end of page! Current page: %d" % ptrPage)
            #fileBytes = "".join(ordToBytes(ordList)) #convert ordList values to bytes
            ac_appendToTextFile(binList, hashID)
            binList = [] #reset binary list

            #debug
            #print("decoder() fileBytes (first 5 elements): " + fileBytes[0:5])
            #print("decoder() fileBytes' length: %d" % len(fileBytes))
            
            ptrPage += 1

            ### Load another pixelData and reset ptrX and ptrY
            pixels = imageToPixel(hashID + "_%d.png" % ptrPage)
            ptrX = 0 + COMP_X
            ptrY = 0 + COMP_Y

            # Extract and update next page number
            pageNum = ac_getPageNumber(pixels)

            #debug
            '''
            print("updated pageNum to: %d" % pageNum)
            print("pixels[2,10]: "), 
            print(pixels[2,10])
            '''

            continue
 
    ### Extract filename of last page of AC pixels ###
    realFilename = ac_getFilename(pixels)

    #debug
    print "ac decoder(): extracted filename: ", realFilename

    ### Convert last set of binary and save decoded data to text file on disk ###
    ac_appendToTextFile(binList, hashID)

    ### Final conversion: Text file to binary(unhexlify)
    ac_appendFinalize(hashID, realFilename)

    ### Clean up
    #cleanUpTempFiles(hashID)

def decoder(origFilename):
    ptrPage = 0         # Current encodedFile page
    pixels = imageToPixel(origFilename + "_%d.png" % ptrPage)
    ptrX = 0+COMP_X     # Starting position
    ptrY = 0+COMP_Y     # Starting position   
    ordList = []

    ### Check header, pixel length, and page number
    # Header @ pixels[2,2] = (100,101,102); pixels[2,3] = (200,201,202)
    if pixels[2,2][0] == 100 and pixels[2,2][1] == 101 and pixels[2,2][2] == 102:
        if pixels[2,3][0] == 200 and pixels[2,3][1] == 201 and pixels[2,3][2] == 202:
            print("Header is valid!")
    else:
        print("Invalid pixelcat Image! Header is invalid")
        exit(1)
    
    # Pixel Length
    pixelLength = pixels[2,4][0]*(256**5) + pixels[2,4][1]*(256**4) + pixels[2,4][2]*(256**3) + pixels[2,5][0]*(256**2) + pixels[2,5][1]*256 + pixels[2,5][2]

    # Extract page number
    pageNum = pixels[2,10][0]*(256**2) + pixels[2,10][1]*256 + pixels[2,10][1]

    #debug
    print("pixelLength: %d" % pixelLength)

    #debug
    print("decoder ptrPage: %d" % ptrPage)

    #fileBytes = ""

    ### Pack pixels data into a ordList[] ###
    for _ in range(pixelLength+1):
        ### Verify if page is in sequence 
        ### TODO: need to check if necessary
        if ptrPage != pageNum:
            print("decoder() error: Page is not decoded in sequence!")
            
            #debug
            print("decoder() ptrPage: %d" % ptrPage)
            print("decoder() pageNum: %d" % pageNum)

            sys.exit(1)

        ### Extracting  (ordinal)
        ordList.append(pixels[ptrY,ptrX][0])
        ordList.append(pixels[ptrY,ptrX][1])
        ordList.append(pixels[ptrY,ptrX][2])

        ### Progress and Adjust Pointers ###
        ptrX += 1

        #Check and adjust X and Y coordinates if there is any spill over
        if ptrX == X2:
            ptrY += 1
            ptrX = 0
    
        if ptrY == Y2:
            #TODO
            print("decoder() end of page! Current page: %d" % ptrPage)
            #fileBytes = "".join(ordToBytes(ordList)) #convert ordList values to bytes
            appendToFile(ordList,origFilename)
            ordList = [] #reset ordList

            #debug
            #print("decoder() fileBytes (first 5 elements): " + fileBytes[0:5])
            #print("decoder() fileBytes' length: %d" % len(fileBytes))
            
            ptrPage += 1

            ### Load another pixelData and reset ptrX and ptrY
            pixels = imageToPixel(origFilename + "_%d.png" % ptrPage)
            ptrX = 0 + COMP_X
            ptrY = 0 + COMP_Y
            # Extract page number
            pageNum = pixels[2,10][0]*(256**2) + pixels[2,10][1]*256 + pixels[2,10][2]

            #debug
            print("updated pageNum to: %d" % pageNum)
            print("pixels[2,10]: "), 
            print(pixels[2,10])

            continue
 
    ### Finally: Convert last set of ordList and save decoded data to disk ###
    appendToFile(ordList, origFilename)

'''**************************** MAIN PROG ******************************'''
'''*********************************************************************'''
def main():
    ### Separate warnings ###
    print("")
    print("")
    
    ''' Parse args (or check for lack thereof) '''
    if len(sys.argv[1:]) == 0:
        parser.print_help()
        parser.exit()
    args = parser.parse_args()

    ''' Switches '''
    if (args.LISTEN): #''' LISTEN (or RECEIVER MODE) '''
        if (args.ANTI_COMPRESSION):
            ac_captureScreen()
        else:
            captureScreen()
    elif (args.ANTI_COMPRESSION):
        ac_encoder(args.FILENAME)
    elif (args.DEBUG): #''' DEBUG ONLY - debugPrintToScreen() '''
        debugPrintToScreen()
    elif (args.CUSTOM): #''' CUSTOM DEBUG - customDebug() '''
        customDebug()
    elif (args.DIAG):
        diagnostics()
    else:
        encoder(args.FILENAME)

    #imageToPixel("/tmp/pixel-screencap.bmp");

    #encoder("bigData.dat")
    
    #decoder("bigData.dat")

    #captureScreen()

if __name__ == "__main__":
    main()
