# Description
Transfer files via screens of GUI remote desktop apps (e.g. RDP, VNC, Citrix, etc)

# Note
- This is only a proof-of-concept code. 
- Currently only the anti-compression mode (-ac) is working well without issues. The original pixelcat (similar function to ptp-rat) feature may not work on certain resolutions (tested on 3440x1440 and encountered issues). 
- Developed and tested on Python 2.7. There are plans to port to python 3.

# Requirements
- (Optional) Recommended to run this via virtualenv, especially on OSX
- For dependencies, view the requirements.txt. To quickly install them:
`pip install -r requirements.txt`
- You need to be able to run full-screen GUI-based remote desktop software (e.g. RDP or Citrix Receiver)

# How to use?
You are required to have the tools present in both sending and receiving hosts, just as you would with a <b>netcat</b> binary. 
#### On Host 'Receiver' PC:
1. Enter the following command to set pixelcat to listening mode (with anti-compression):
`python pixelcat.py -l -ac`
2. Your pixelcat program should be silently taking screenshots and detecting for pixelcat headers on screen.

-l: switch to listening
-ac: anti-compression mode

#### On Target 'Sender' PC:
1. Proceed to log in via the chosen remote desktop program to the target PC that contains the file to be exfiltrated. 
2. Set remote desktop program to full screen mode.
3. To start the transmission, enter the following command:
`python pixelcat.py -ac -i <filename.ext>`
4. Pixelcat should start splashing images to the screen. Allow it to complete.
5. Return back to the host PC. Examine the pixelcat messages on console and you should observe a new file saved.

-i: input mode, and to specify directory and filename

#### Advance Configurations
For further tweaking, you may examine the 'pixelcat.py' file and do some tweaking to the various variables below:
###### Notch Compensation
COMP_Y: Offset from the top. A value of 32 means the splashed images are shifted 32 pixels downwards.
###### Bandwidth Compensation
BANDWIDTH_COMP: Default value is 0. Set positive value to reduce the splashed images. This is useful for situations where bandwidth is very limited. Setting a value of 500 means 500 pixels from bottom will not be used for splashed images. This should assist in reducing latency that could cause synchronization issue. 
###### Capture Intervals & Splash Period
CAPTURE_INTERVAL: Default value is 2. This sets the captures between intervals. 
SPLASH_PERIOD: Default value is 2. This sets how long the splashed images are retained on screen. 

#### Accuracy
The anti-compression mode is not a lossless mode. The accuracy of the file integrity depends heavily on the bandwidth and compression level. The better the connection, the higher the accuracy. The average accuracy should about around 98% over the Internet at a typical modern bandwidth.

#### Help
`python pixelcat.py -h`

# Credits
Special thanks to PentestPartners for the idea and inspiration. This concept was first published by PentestPartners:
https://www.pentestpartners.com/security-blog/exfiltration-by-encoding-data-in-pixel-colour-values/
