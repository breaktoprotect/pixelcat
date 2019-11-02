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
#### On Host 'Receiver' PC:
Enter the following command to set pixelcat to listening mode (with anti-compression):
`python pixelcat.py -l -ac`

-l: switch to listening
-ac: anti-compression mode
#### On Target 'Sender' PC:
`python pixelcat.py -ac -i <filename.ext>`

-i: input mode, and to specify directory and filename

#### Help
`python pixelcat.py -h`

# Credits
Special thanks to PentestPartners for the idea and inspiration. This concept was first published by PentestPartners:
https://www.pentestpartners.com/security-blog/exfiltration-by-encoding-data-in-pixel-colour-values/
