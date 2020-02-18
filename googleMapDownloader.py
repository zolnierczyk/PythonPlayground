#!/usr/bin/python

import urllib
from PIL import Image
import os
import math
from geographiclib.geodesic import Geodesic
import time

class GeoPoint:
    def __init__(self, lat, lon):
        self._lat = lat
        self._lon = lon

class GoogleMapDownloader:
    def __init__(self, upperLeft, bottomRight, zoom):
        self._upperLeft = upperLeft
        self._bottomRight = bottomRight
        self._zoom = zoom
        self._urlbase = 'https://maps.googleapis.com/maps/api/staticmap?size=640x640&maptype=satellite&zoom=' + str( self._zoom)
        self._tileSize = 640
        self._geod = Geodesic.WGS84 
        self.calculateResolution()
        
    def calculateResolution(self):
        self._meterPerPixel = 156543.03392 * math.cos(self._upperLeft._lat * math.pi / 180) / math.pow(2, self._zoom)
        print("Map resolution for zoom level={0} is {1} m/pix".format(self._zoom, self._meterPerPixel))
        
    def fechMapFromGoogle(self, lon, lat):
        url = self._urlbase + '&center=' + str(lat) + ',' + str(lon)
        print('Fetching url {0}'.format(url))
        current_tile = 'part_{0}-{1}'.format(lat, lon)
        urllib.urlretrieve(url, current_tile)
        time.sleep(0.5)
        return current_tile
        
    def generateImage(self):

        # Determine the size of the image
        distanceLon = self._geod.Inverse(self._upperLeft._lat, self._upperLeft._lon, self._upperLeft._lat, self._bottomRight._lon)
        distanceLat = self._geod.Inverse(self._upperLeft._lat, self._upperLeft._lon, self._bottomRight._lat, self._upperLeft._lon)

        widthMeters = distanceLon['s12'] 
        heightMeters = distanceLat['s12'] 
        print("Area size in meters width: {0} height:{1}".format(widthMeters, heightMeters))
        width = math.ceil(widthMeters / self._meterPerPixel)
        height = math.ceil(heightMeters / self._meterPerPixel)
        print("Image size in pixels width: {0} height:{1}".format(width, height))

        #Create a new image of the size require
        map_img = Image.new('RGB', (int(width), int(height)))
        
        nrOfTilesToFetchHorizontal = int(math.ceil(width / self._tileSize ))
        nrOfTilesToFetchVertical = int(math.ceil(height / self._tileSize ))
        print("Will fetch number tiles of x:{0} y:{1}".format(nrOfTilesToFetchHorizontal, nrOfTilesToFetchVertical))

        diagonal = math.sqrt(2.0)*self._tileSize * self._meterPerPixel / 2.0
        deltaDistance = self._tileSize * self._meterPerPixel
        print("Step size in meter: {0} and diagonal: {1}".format(deltaDistance, diagonal))
        centerTrans = self._geod.Direct(self._upperLeft._lat, self._upperLeft._lon, 135, diagonal)
        upperLeftRootCenterLon = centerTrans['lon2']
        upperLeftRootCenterLat = centerTrans['lat2']
        outputImgX = 0
        outputImgY = 0

        upperLeftCenterLon = upperLeftRootCenterLon
        upperLeftCenterLat = upperLeftRootCenterLat
        for i in range(1, nrOfTilesToFetchHorizontal*nrOfTilesToFetchVertical + 1): 
            print("Extracting tile :{0}".format(i))
            rootTile = self.fechMapFromGoogle(upperLeftCenterLon, upperLeftCenterLat)
            im = Image.open(rootTile)
            print("Past onto image x:{0} y:{1}".format(outputImgX, outputImgY))
            map_img.paste(im, (outputImgX, outputImgY))
            os.remove(rootTile)
            if (i % nrOfTilesToFetchHorizontal == 0):
                print("Moving next row")
                upperLeftCenterLon = upperLeftRootCenterLon
                centerTrans = self._geod.Direct(upperLeftCenterLat, upperLeftCenterLon, 180, deltaDistance)
                upperLeftCenterLon = centerTrans['lon2']
                upperLeftCenterLat = centerTrans['lat2']
                outputImgY = outputImgY + self._tileSize
                outputImgX = 0
            else:
                print("Moving next column")
                centerTrans = self._geod.Direct(upperLeftCenterLat, upperLeftCenterLon, 90, deltaDistance)
                upperLeftCenterLon = centerTrans['lon2']
                upperLeftCenterLat = centerTrans['lat2']
                outputImgX = outputImgX + self._tileSize

        return map_img

def main():

    #zoom level=16 is 1.46893444681 m/pix
    #zoom level=17 is 0.734467223406 m/pix

    # Tor kosciuszko
    upperLeft = GeoPoint(50.070309, 20.148801)
    bottomRight = GeoPoint(50.066805, 20.152602)

    # Millbroke
    #upperLeft = GeoPoint(52.050808, -0.555724)
    #bottomRight = GeoPoint(52.034967, -0.524869)
    
    gmd = GoogleMapDownloader(upperLeft, bottomRight, 17)

    try:
        # Get the high resolution image
        img = gmd.generateImage()
    except IOError:
        print("Could not generate the image - try adjusting the zoom level and checking your coordinates")
    else:
        #Save the image to disk
        img.save("Map_{0}-{1}.png".format(gmd._upperLeft._lat, gmd._upperLeft._lon))
        print("The map has successfully been created")


if __name__ == '__main__':  main()
