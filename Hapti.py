#INPUT: image, drop percentage, color reducer number
# OUTPUT: for every color: A STL file with the image as a layer 

import os
import argparse
from PIL import Image
import colorsys
from subprocess import call
import fileinput


###
# EN:
descr = 'generates STL files for each major color in the image'
hintcolorreducing = 'HINT:\tIf the colors looks strange to you, try a higher or lower number of colors'
hintcolorauto = 'HINT:\tinteractive color reduction enabled, to disable use the --colors argument'
hintcolorauto2 = '\nLook at temp2.png ... temp15.png. Choose the image with the lowest number that still looks similar to the source image'
asknumber = "Please enter the chosen number: "
hintcolormanual = 'HINT:\tIf you want to run with this number of colors again, use --colors '
warningtoomanycolors = 'WARNING:\tNo major colors, please run color-reducer first!'
hintdespecklingtime = 'HINT:\tDespeckling enabled, this could take some time...'
hintdespecklingradius = 'HINT:\tIf you still see some spots or fine lines, increase despeckling radius'
hinteditingfiles = 'HINT:\tYou can edit the saved files if you like!'
hintinkscapeopen = 'HINT:\tInkscape will open and close a few times.'
inkscapefirstrun = 'HINT:\tBefore you run this script for the first time, please make sure to install the inkscape paths2openscad extension'
hintoffset = 'HINT\tIf a layer is shifted in the model, try to increase the despeckling radius'
###

# command line options
parser = argparse.ArgumentParser(description=descr)
parser.add_argument("image",type=argparse.FileType('r'), help = "Input image")
parser.add_argument("-d", "--drop", type=float, default=1, help = "drop percentage, default: 1")
parser.add_argument("-c", "--colors", type=int, default=42, choices=range(0, 16), help = "number of colors for manual reduction, 0 for no reduction")
parser.add_argument("-k", "--despeckle", type=int, default=0, choices=range(0, 5), help = "despeckling radius: will improve quality, but will take more time. Start with a low value.")
parser.add_argument("-s", "--scale", type=float, default=(0.1), help = "Model Scale in mm/pixel, default 0.1")
parser.add_argument("-t", "--thickness", type=float, default=(0.5), help = "Layer thickness in mm, default: 0.5")
parser.add_argument("-kf", "--keepfiles", help="Keep intermediate files", action="store_true") # if added, args.keepfiles = True
# zB args.drop usw
args = parser.parse_args()

# read image
im = Image.open(args.image)
basename = os.path.splitext(args.image.name)[0]
# convert to RGB if not in RGB
if not ((im.mode) is 'RGB' or (im.mode) is 'RGBA'):
	im = im.convert("RGB",dither=None)

# color reduction - interactive
# non-user available value of colors for default interactive mode
if args.colors == 42:
	print hintcolorauto
	print hintcolorauto2
	for k in range(2,16):
		newfilename = 'temp' + str(k) + '.png'
		callstring = 'convert +dither ' + args.image.name + ' -colors ' + str(k) +  ' ' + newfilename
		call(callstring,shell=True)
	chosennumber = int(input(asknumber))
	im = Image.open('temp' + str(chosennumber) + '.png')
	print hintcolormanual + str(chosennumber)
	# remove temp files
	for k in range(2,16):
		os.remove('temp' + str(k) + '.png')

# color reduction - manual
if not (args.colors == 0) and not (args.colors == 42):
	# run imagemagick to reduce colors and read that image instead of the source one
	newfilename = 'temp.jpg' 
	# run imagemagick
	callstring = 'convert +dither ' + args.image.name + ' -colors ' + str(args.colors) +  ' ' + newfilename
	call(callstring,shell=True)
	im = Image.open(newfilename)
	# remove colorreduced file
	os.remove(newfilename)

# convert to RGB if not in RGB
if not ((im.mode) is 'RGB' or (im.mode) is 'RGBA'):
	im = im.convert('RGB',dither=None)

#get colors from image
colors=im.getcolors(im.size[0]*im.size[1])
# sort colors, most common colors first
colors.sort(reverse=True)


# set threshold for drop in pixels
threshold = 0.01*args.drop*im.size[0]*im.size[1]
# workaround for small images
if threshold < 1:
	threshold = 1

# get major colors 
j = 0
majorcolors = []
# only those colors which make more than 1% of the image pixels are major colors
while (colors[j][0] >= threshold):
	majorcolors.append(colors[j][1])
	j=j+1
	if j == len(colors):
		break
# catch if majorcolors still empty
if majorcolors == []:
	print(warningnomajorcolors)
	quit()

# convert majorcolors to HSV
#initialize majorcolorshsv
majorcolorshsv = []
for i in range(len(majorcolors)):
	majorcolorshsv.append(colorsys.rgb_to_hsv(majorcolors[i][0]/255.0, majorcolors[i][1]/255.0, majorcolors[i][2]/255.0))
	# ! output values are decimal, to get normal HSV multiply by 360, 100, 100

# replace pixels with non-major color with nearest major color
pixels=im.load()
width, height = im.size
for i in range(width):
	for j in range(height):
		# convert color value of pixel to HSV
		pixelhsv = colorsys.rgb_to_hsv(pixels[i,j][0]/255.0,pixels[i,j][1]/255.0, pixels[i,j][2]/255.0)
		if pixelhsv not in majorcolorshsv:
			# compute majorcolor with least distance
			# max distance as first value
			dmin=3*(255**2)
			for k in range(0,len(majorcolorshsv)):
				# use simple squared euclidean distance
				d= (pixelhsv[0]-majorcolorshsv[k][0])**2 + (pixelhsv[1]-majorcolorshsv[k][1])**2 + (pixelhsv[2]-majorcolorshsv[k][2])**2
				if d < dmin:
					dmin = d
					# replace pixelcolor with majorcolor
					pixels[i,j]=majorcolors[k]	
# save image
im.save(os.path.splitext(args.image.name)[0] + '.step1.png')
print hintcolorreducing

# read just saved image
basename = os.path.splitext(args.image.name)[0]
im = Image.open(basename + '.step1.png')
# convert to RGB if not in RGB
if not ((im.mode) is 'RGB' or (im.mode) is 'RGBA'):
	im = im.convert("RGB",dither=None)

# sort colors, most common colors first
colors=im.getcolors(im.size[0]*im.size[1])
colors.sort(reverse=True)

# print text file with every color
# with ... closes and opens file
# delete old -colors.txt
if os.path.exists(basename+ '-colors.txt'):
    os.remove(basename + '-colors.txt')
with open(basename + '-colors.txt', 'w') as colormap:
	for k in range(len(colors)):
		# write colors as rgb tupels
		colormap.write( str(colors[k][1]) + '\n')

# for every color: generate an image where this color is black and all others are white
width, height = im.size
if args.despeckle > 0:
	print hintdespecklingtime
for k in range(len(colors)):
	im = Image.open(basename + '.step1.png')
	pixels=im.load()
	# walk through image and color black and white
	for i in range(width):
		for j in range(height):
			if pixels[i,j] == colors[k][1]:
				pixels[i,j] = (0,0,0)
			else:
				pixels[i,j] = (255,255,255)
	# try simple despeckling (TODO: this is very inefficient, recursive?)
	# define despeckling radius function
	def score(i,j,d):
		pixelscore = 0
		for k in range(max(0,i-d),min(i+d+1, width)): # x: i-d ... i+d
			for l in range(max(0,j-d),min(j+d+1, height)): # y: j-d ... j+d
				pixelscore = pixelscore + pixels[k,l][0]/255
		threshold= ((min(i+d+1, width)-max(0,i-d))*(min(j+d+1, height)-max(0,j-d)))*0.50 # 50% of all checked pixels
		# if lower then threshold black, else white
		if  pixelscore < threshold:
			score = 0
		else:
			score = 1
		return score
	# despeckling radius
	d = args.despeckle
	if args.despeckle > 0:
		for i in range(0,width): # x
			for j in range(0,height): # y
				# score: number of pixels in neighborhood (d) which are white, ranges from 0 to (d+(d+1))^2, ex d=1 -> 9, d=2 -> 25
				# this is very inefficient and ignores the d pixels on the edge of the image (potrace removes them as turds)
				if score(i,j,d) == 0:
					pixels[i,j] = (0,0,0)
				elif score(i,j,d) == 1:
					pixels[i,j] = (255,255,255)
	im.save(basename + '.color' + str(k+1) + '.bmp')

print hintdespecklingradius
print hinteditingfiles

# get number of images: check number of lines in basename-colors 
imagenumber = (sum(1 for line in open(basename + '-colors.txt')))
# for every BMP file in current folder run potrace and generate an SVG
for p in range(1,imagenumber+1): # 1...imagenumber
	file = basename + '.color' + str(p) + '.bmp'
	callstring = 'potrace --svg ' + file + ' -a 0 -t 20 --group --flat'
	call(callstring,shell=True)
	im = Image.open(file)
	width, height = im.size
# for every SVG make a layer of layerthickness with paths2openscad
print hintinkscapeopen
print inkscapefirstrun
hintmodelsize = 'HINT:\tWith this scale, the model will be ' + str(round(width * args.scale)) + ' x ' + str(round(height * args.scale)) + 'mm. To change this, use the scale parameter.'
print hintmodelsize

# modify settings for paths2openscad in inkscape settings file
# callstring ='inkscape --verb=command.extrude.openscad'
# call(callstring,shell=True)s
# for line in fileinput.input('~/.config/inkscape/preferences.xml', inplace=True): 
#       print line.rstrip().replace('command.extrude.openscad.height="5"', 'command.extrude.openscad.height="2"'),
# actually dont meddle in the XML settings file, just move the layer files to the work folder
# according to paths2openscad.inx the default filename is ~/inkscape.scad

# run paths2openscad for every SVG in the folder, keep paths2openscad standard settings
for p in range(1,imagenumber+1): # 1...imagenumber
	file = basename + '.color' + str(p) 
	callstring = 'inkscape --verb=command.extrude.openscad.noprefs ' + file + '.svg' + ' --verb=FileQuit'
	call(callstring, shell=True)
	# move the file to the current workfolder
	oldpath = os.path.expanduser("~") + "/inkscape.scad"
	newpath = os.getcwd() + '/' +  file  + '.scad'
	os.rename(oldpath, newpath)
# TODO: maybe merge this with the next block?

# replace height in mm and profile_scale (in mm/px, default 0.1) in scad files
print 'HINT:\tThe 3D model will be the size (W x H), mm: ' + str(round(width * args.scale)) + ' x ' + str(round(height * args.scale))
for p in range(1,imagenumber+1): # 1...imagenumber
	file = basename + '.color' + str(p) + '.scad'
	for line in fileinput.input(file, inplace=True): 
		print line.rstrip().replace('height = 5;', 'height = ' + str(args.thickness) + ';')
	for line in fileinput.input(file, inplace=True): # for some reason these need to be in seperate loops
		print line.rstrip().replace('profile_scale = 25.4/90; //made in inkscape in mm', 'profile_scale = ' + str(args.scale) + ';')

# move layers in the scad file to their location in the image 
def boxinl():
# search from left
	for i in range(width):
		for j in range(height):
			if pixels[i,j] == (0,0,0):
				# pixels[i,j] = (255,0,0)
				return (i,j)

def boxind():
# search from down
	for j in range(height-1,-1,-1): # from height -1 down to 0
		for i in range(width):
			if pixels[i,j] == (0,0,0):
				# pixels[i,j] = (255,0,0)
				return (i,j)

def boxinr():
# search from right
	for i in range(width-1,-1,-1):
		for j in range(height-1,-1,-1):
			if pixels[i,j] == (0,0,0):
				# pixels[i,j] = (255,0,0)
				return (i,j)

def boxinu():
# search from up
	for j in range(height):
		for i in range(width-1,-1,-1):
			if pixels[i,j] == (0,0,0):
				# pixels[i,j] = (255,0,0)
				return (i,j)

def boxcorners():
	return(min(boxinl()[0],boxind()[0],boxinr()[0],boxinu()[0]),min(boxinl()[1],boxind()[1],boxinr()[1],boxinu()[1]),max(boxinl()[0],boxind()[0],boxinr()[0],boxinu()[0]),max(boxinl()[1],boxind()[1],boxinr()[1],boxinu()[1]))

# read the positions for the images (box around the black part, lower left and upper right corner)
for p in range(1,imagenumber+1): # 1...imagenumber
	file = basename + '.color' + str(p) + '.bmp'
	im = Image.open(file)
	width, height = im.size
	pixels=im.load()
	imagecorners = boxcorners() # eg. (189,30, 199, 40) first two are lower left corner, last two upper right corner
	imagecenter = ((imagecorners[0]+imagecorners[2])/2.0,(imagecorners[1]+imagecorners[3])/2.0) # center of the image
# put translation in scad file
	file = basename + '.color' + str(p) + '.scad'
	for line in fileinput.input(file, inplace=True): 
		replacestring = 'module poly_path8(h, w, res=4)  {\n  translate([' + str((imagecenter[0] - 0.5* width)*args.scale) + ', ' + str((imagecenter[1] - 0.5* height)*-args.scale) + ', 0])'
		print line.rstrip().replace('module poly_path8(h, w, res=4)  {', replacestring)
print hintoffset

# produce stl files with openscad
# for p in range(1,imagenumber+1): # 1...imagenumber
# 	file = basename + '.color' + str(p)
# 	callstring = 'openscad ' + file + '.scad' + ' -o ' + file + '.stl'
# 	call(callstring, shell=True)		
# remove SVG, scad files if the keepfiles switch is not set
if args.keepfiles == False:
	for p in range(1,imagenumber+1): # 1...imagenumber
		file = basename + '.color' + str(p)
		os.remove(file + '.svg')
		os.remove(file + '.bmp')
		# os.remove(file +  '.scad')