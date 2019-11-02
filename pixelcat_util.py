''' pixelcat's Utility module '''
import sys
import binascii
import scipy.misc as smp
from PIL import Image, ImageTk
import numpy
import os
import glob

### PIXEL ERROR CORRECTION THRESHOLD
ZERO_THRESHOLD = 120 #must be less than this value
ONE_THRESHOLD = 130 #nust be more than this value

""" Converts integer to pixel representation """
### e.g. int 300 is pixel[y,x]'s (0,1,44) for pix_size=1
###      Represents as n[2]=44, n[1]=1, n[0]=0
##       Position [0, 5, 20] of pixel is pixel[0]=0, pixel[1]=5, pixel[2]=20
##       Position [c, b, a ]
##       Position (pixel[0], pixel[1], pixel[2])
def intToPixel(intg,pix_size):
    # Check pixel size: Max 2 for now, min 1
    if pix_size < 1 or pix_size > 2:
        print("intToPixel() Error: pix_size should be between 1 and 2.")
        sys.exit(1) #error/issue exit

    cur_size = 0    #track how many pixel color elements needed (RGB)
    n = []          #resultant pixel representation
    while(True):
        if (intg > 256):
            n.append(intg % 256)
            intg = intg / 256
            cur_size += 1
        elif (intg == 256):
            n.append(1)
            cur_size +=1
            break
        else:
            n.append(intg % 256)
            break

    # Check if converted pixel rep of the integer is too large
    if cur_size > (pix_size*3):
        print("intToPixel() Error: integer is too large. Not supported.")
        sys.exit(1)

    #debug
    print("intToPixel() intg: %d" % intg)
    print("     cur_size = %d" % cur_size)
    
    # Make the list at least 6 n
    for _ in range((pix_size*3)-len(n)):
        n.append(0)

    #debug
    print("intToPixel() returning n:"),
    print(n)

    return n

""" AC version Set Header"""
#@@ Sets the signature/magic header
#@@ Gets the pixels and returns the same pixels with magic header set
def ac_setMagicHeader(pixels):
    for y in range (0,4):
        if y % 2 == 1:
            continue
        for x in range (0,4):
            if x % 2 == 0:
                pixels[1+y,x] = (0,0,0)
            else:
                pixels[1+y,x] = (255,255,255)
    return pixels

""" AC version Detect Header """
#@@ Detect the signature/magic header
#@@ Returns true or false
#@@ Remarks: It's not a total check, so if cranky may need to make it more robust.
def ac_detectMagicHeader(pixels):
    for y in range (0,4):
        if y % 2 == 1:
            #Check that all pixels are dark
            for z in range (0, 4):
                if ac_estimatePixelStr(pixels[1+y,z]) != '0':
                    return False
            continue
        for x in range (0,4):
            if x % 2 == 0:
                # Check if pixels are dark (0,0,0)
                if ac_estimatePixelStr(pixels[1+y,x]) != '0':
                    return False
            else:
                # Check if pixels are bright (255,255,255)
                if ac_estimatePixelStr(pixels[1+y,x]) != '1':
                    return False
    return True #return True if all checks are passed 

""" AC version Set the Binary Length on Pixels """
#@@ Set the total length of file to be expected on pixels
#@@ Returns a pixel numpy array
def ac_setLength(intLength, pixels):
    # Convert int length to binary rep
    binLength_ = bin(intLength)
    binLength = binLength_[2:]

    # Pre-pend 0s in front
    zeroFills = 40 - len(binLength)
    for _ in range(0,zeroFills):
        binLength = '0' + binLength

    #debug
    print(str(intLength) + " is: " + binLength)

    # Check that binLength is within 40 bits
    if len(binLength) > 40:
        print("[-] Error: File size too long!")
        sys.exit(1)

    # Update the binary length to pixels
    for x in range(0,len(binLength)):
        if binLength[x] == '1':
            pixels[4,x] = (255,255,255)
        else:
            pixels[4,x] = (0,0,0)  

    return pixels

""" AC version Detect Binary Length """
#@@ Detects the total length of file from pixel
#@@ Returns integer
def ac_getLength(pixels):
    binLength = []

    for x in range(0,40):
        binLength.append( ac_estimatePixelStr(pixels[4,x]) )
    
    """
    for x in range(0,40):
        if numpy.array_equal(pixels[4,x], (255,255,255)):
            binLength.append('1')
        else:
            binLength.append('0')
    """

    

    binLengthStr = ''.join(binLength)

    #debug
    #print "ac_detectLength() binLength: ", binLengthStr

    intLength = long(binLengthStr,2)

    return intLength

""" AC version Set Page Number """
#@@ Sets the current page number on pixels at position [5,0 to 20]
#@@ Returns pixel
#@@ 20 bits
def ac_setPageNumber(pageNum, pixels):
    # Convert page number to binary rep
    binPage_ = bin(pageNum)
    binPage = binPage_[2:]

    #Pre-pends 0s in front
    zeroFills = 20 - len(binPage)
    for _ in range(0,zeroFills):
        binPage = '0' + binPage

    #debug
    print("ac_setPageNumber() - binary rep of page number: ", binPage)

    # Check that binPage is within 20 bits
    if len(binPage) > 20:
        print("[-] Error: Page number size too big!")
        sys.exit(1)

    # Update the binary length to pixels
    for x in range(0,len(binPage)):
        if binPage[x] == '1':
            pixels[5,x] = (255,255,255)
        else:
            pixels[5,x] = (0,0,0)  
    
    return pixels
    
""" AC version Get Page Number """
#@@ Gets the page number from pixels at position [5,0 to 19]
#@@ Returns Pixel
#@@ 20 bits
def ac_getPageNumber(pixels):
    binPage = []

    for x in range(0,20):
        binPage.append( ac_estimatePixelStr(pixels[5,x]) )

    """
    for x in range(0,20):
        if numpy.array_equal(pixels[5,x], (255,255,255)):
            binPage.append('1')
        else:
            binPage.append('0')

    """

    binPageStr = ''.join(binPage)

    #debug
    print "ac_detectLength() binPage: ", binPageStr

    pageNum = long(binPageStr,2)

    return pageNum

""" Pixel to Integer """
##       Position [0, 5, 20] of pixel is pixel[0]=0, pixel[1]=5, pixel[2]=20
##       Position [c, b, a ]
##       Position (pixel[0], pixel[1], pixel[2])
def pixelToInt(pixels):
    #debug
    print("pixels:"),
    print(pixels)


    a = pixels[2]
    b = pixels[1] * 256
    c = pixels[0] * 256 * 256

    #debug
    print("firstOrder: " + str(a))
    print("secondOrder: " + str(b))
    print("thirdOrder: " + str(c))

    return a + b + c

""" AC version Set Last Page header """
#@@ Setting 'last page' header from pixel[11,0 to 9]
def ac_setLastPage(pixels):
    binStr = "0101010101" 
    
    for x in range(0,10):
        if binStr[x] == '1':
            pixels[11,x] = (255,255,255)

    return pixels 

""" AC version Detect Last Page Header """
#@@ Setting 'last page' header from pixel[11,0 to 9]
def ac_detectLastPage(pixels):
    for x in range(0,10):
        if x % 2 == 0 and ac_estimatePixelStr(pixels[11,x]) == '0':
            continue
        elif x % 2 == 1 and ac_estimatePixelStr(pixels[11,x]) == '1':
            continue
        else:
            return False
    return True


""" AC version Set Filename """
#@@ Sets the filename on the pixel at positions[6-11,0-500] where max character is 260
#@@ Returns pixel
def ac_setFilename(filename, pixels):
    ### Check for filename length (must be less than or equal to 260)
    if len(filename) > 260:
        print "[-] Fatal error: Filename too long! Should be less than or equal to 260 characters."
        sys.exit(1)

    binFilename_ = bin(int(binascii.hexlify(filename),16))
    binFilename = binFilename_[2:]

    #debug before zerofill
    #print "ac_setFilename() binFilename before zerofills: ", len(binFilename)

    ### Pack it to fill all gaps by prepending 0
    zeroFills = (500*5) - len(binFilename)
    for _ in range(0,zeroFills):
        binFilename = '0' + binFilename

    #debug after zerofills
    #print "ac_setFilename() binFilename after zerofills: ", len(binFilename)

    ptrY = 6 #starts from 6, max is 11
    ptrX = 0 #starts from 0, max is 500

    for bit in binFilename:
        if (bit == '1'):
            pixels[ptrY, ptrX] = (255,255,255) 
        ptrX += 1 

        # Check for X boundary
        if ptrX == 500:
            ptrX = 0 #resets
            ptrY += 1

    #debug
    #print("ac_setFilename() binFilename: ", binFilename)
    #print("ac_setFilename() length of filename: ", len(filename))
    #print("ac_setFilename() length of binFilename: ", len(binFilename))

    return pixels

""" AC version Get Filename """
#@@ Retrieve filename on pixels
#@@ Return string
def ac_getFilename(pixels):
    binFilename = []

    totalPixels = 500*5
    ptrY = 6
    ptrX = 0

    for _ in range(0,totalPixels):
        binFilename.append( ac_estimatePixelStr(pixels[ptrY,ptrX]) )
        """
        if numpy.array_equal(pixels[ptrY,ptrX], (255,255,255)):
            binFilename.append('1')
        else:
            binFilename.append('0')
        """
        
        ptrX += 1

        # Check for X boundary
        if ptrX == 500:
            ptrX = 0 #resets
            ptrY += 1

        if ptrY == 11 and ptrX == 1:
            print "[-] Fatal error: Seek out of bounds for filename pixels region"

    binFilename = ''.join(binFilename)

    #debug
    #print "ac_getFilename() binFilename (populated): ", binFilename
    #print "    ptrY = ", ptrY
    #print "    ptrX = ", ptrX

    filename = binascii.unhexlify('%x' % int(binFilename,2))

    return filename

""" AC version estimation logic gate """
#@@ Determine if pixel is white or black pixel then 
#@@     return '1' or '0' respectively
#@@ Takes in ONE pixel, not pixel numpy array
#@@ *** HIGHLY EXPERIMENTAL ***
def ac_estimatePixelStr(aPixel):
    if aPixel[0] < ZERO_THRESHOLD:
        return '0'
    else:
        return '1'

#@@ Returns ONE pixel either (0,0,0) or (255,255,255)
def ac_estimatePixel(aPixel):
    if aPixel[0] < ZERO_THRESHOLD:
        return (0,0,0)
    else:
        return (255,255,255)

#@@ Diagnostics tool
def ac_outOfThreshold(aPixel):
    if aPixel[0] > ZERO_THRESHOLD and aPixel[0] < ONE_THRESHOLD:
        print "ac_outOfThreshold() anomaly detected!", aPixel

""" Convert ordList into byte list """
### Returns byte list that can be printed or saved into a file
def ordToBytes(ordList):
    ### Reconstructing ordList back to bytes
    hexData = ""
    for x in range(len(ordList)):
        #hex_0x = hex(ordList[x])
        hex_0x = "0x{:02x}".format(ordList[x])

        #debug 
        #print("ord: %d " % ordList[x]),
        #print("hex_0x: " + hex_0x)

        hex_true = hex_0x.replace("0x","")

        hexData += hex_true

    byteData = binascii.unhexlify(hexData)
    return byteData

""" Flush decoded data into disk """
def saveToFile(dataBytes, filename):
    ### Convert ordList to bytes
    #byteList = ordToBytes(ordList)

    ### Saving the bytes to file
    f = open("decoded_" + filename,"wb") #test safety catch to prevent overwriting of originals
    f.write(dataBytes)
    f.close()

""" Partially flush data into disk """
def appendToFile(ordList, filename):
    ### Convert ordList to bytes
    byteList = ordToBytes(ordList)

    ### Saving the bytes to file
    f = open("decoded_" + filename,"ab") #test safety catch to prevent overwriting of originals
    f.write(byteList)
    f.close()

""" AC version Partially flush data into disk as Text file """
#@@ Intermediary step before converting the "00101010101001111100" to an actual binary
#@@ To fix split-binary between pages issue
def ac_appendToTextFile(binList, filename):

    ### Convert list to a single binary represented string
    binStr = "".join(binList)

    ### Saving bin rep to text file
    f = open(filename + ".dat","ab") #test safety catch to prevent overwriting of originals
    f.write(binStr)
    f.close()

""" AC version Finally convert Binary rep text file to actual Binary """
#@@ Final step of decoding
def ac_appendFinalize(hashID, realFilename):
    ### Open binary represented text file
    f = open(hashID + ".dat", "rb" ).read()

    byteList = binascii.unhexlify('%x' % int(f,2))

    ### Saving the bytes to file
    f = open("decoded_" + realFilename,"wb") 
    f.write(byteList)
    f.close()

""" Clean up temporary files """
### Input hashID
def cleanUpTempFiles(hashID):
    try:
        for fl in glob.glob("*" + hashID + "*"):
            os.remove(fl)

            #debug
            print("*** Removing " + fl)
        
        print("[+] Cleaned up!")

    except Exception as exception:
        print("[-] Error removing files.")
        print str(exception)   


""" Grab file from disk, then convert to numpy pixel array """
def imageToPixel(imgFilename):
    img = Image.open(imgFilename)
    pixels = numpy.asarray(img)
    
    #TODO:verification check if it is a pixel-encoded data file
   
    return pixels