# Hapti.py

This is a small python2 script to turn images into a stack of 3d-printable layers.

## 1 Installation

Note: These instructions are written for Ubuntu 16.04, the steps for your distribution might be different.

You need the following packages:

* Python 2
* imagemagick
* inkscape
* potrace
* freecad (optional, for viewing and stacking the .stl files)

As python2 and imagemagick are preinstalled in Ubuntu 16.04 you only need to install the others:

```
sudo apt-get install inkscape potrace freecad openscad
```

Now install the paths2openscad extension for Inkscape from [here](https://www.thingiverse.com/thing:1065500), open the zip file "paths2openscad-7.zip" and place its contents in your local Inkscape extension folder,

```
~/.config/inkscape/extensions/
```
Note: You might have to start Inkscape for the first time for the folders to be created.

If you open Inkscape now, there should be a new entry "Paths to OpenSCAD" under Extensions -> Generate from Path. Don't change the location of the output file, the script will handle that for you.

## 2 A first Example

Now, let's try it out! Download [this](https://openclipart.org/image/800px/svg_to_png/247297/TJ-Openclipart-58-tulips-in-a-pot-22-4-16---final.png&disposition=attachment) image and rename it to test.png. Then, place Hapti.py and test.png in a new folder and point a terminal to that folder.

Now we want to create a 15cm big print, so we set the scale switch to 150/800=0.1875 mm/pixel. Also, we want some despeckling with a radius of two pixels. So our command is

```
python Hapti.py -k 2 -s 0.1875 test.png
```

Now follow the on-screen instructions, the warning about RGBA images can be safely ignored (Note: To remove the warning, just replace the transparency in the image with another color in GIMP). In this case, the script will take about 5-10 minutes.

Let's say you want to have a different height for all our color layers. To change the height of a part, just open the corresponding .scad file and change the height parameter in line 22. Then, press F6 to render the part and export it as an .STL file with the STL button.

At last, you can open the created .STL files in FreeCAD and just copy all parts into a new file to stack them.

## 3 Some worked examples

The source images are derived from [this](https://openclipart.org/detail/247297/tulips-in-a-pot-just-random) one.

## 4 Command-line help

```
usage: Hapti.py [-h] [-d DROP] [-c {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}]
                [-k {0,1,2,3,4}] [-s SCALE] [-t THICKNESS] [-kf]
                image

generates STL files for each major color in the image

positional arguments:
  image                 Input image

optional arguments:
  -h, --help            show this help message and exit
  -d DROP, --drop DROP  drop percentage, default: 1
  -c {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}, --colors {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}
                        number of colors for manual reduction, 0 for no
                        reduction
  -k {0,1,2,3,4}, --despeckle {0,1,2,3,4}
                        despeckling radius: will improve quality, but will
                        take more time. Start with a low value.
  -s SCALE, --scale SCALE
                        Model Scale in mm/pixel, default 0.1
  -t THICKNESS, --thickness THICKNESS
                        Layer thickness in mm, default: 0.5
  -kf, --keepfiles      Keep intermediate files
```
