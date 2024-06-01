import cv2 as cv
import numpy as np
import math

def drawBead(baseX, baseY, boundBoxLength, img, r1, r2, padding):
    cx = baseX + boundBoxLength//2 + padding
    cy = baseY + boundBoxLength//2 + padding
    for i in range(boundBoxLength):
        for j in range(boundBoxLength):
            x = baseX + i
            y = baseY + j
            height, width, depth = img.shape
            if(x < 0 or y < 0 or x >= height or y >= width):
                continue
            dist = math.sqrt(pow(cx - x, 2) + pow(cy - y, 2))
            if(dist > r1 and dist < r2 ):
                img[x, y] = (255, 255, 255)

def main():

    #bead shape parameters
    innerRadius = 15 #in pixels
    outerRadius = 34
    padding = 2
    boundBoxLength = (outerRadius + padding) * 2
    xDisplacement = int(round(math.sqrt(3*pow(outerRadius, 2) + (3 * outerRadius * padding) + 3 * pow(padding, 2))))

    #texture shape parameters
    beadsWidth = 30
    width = boundBoxLength * beadsWidth
    height = (width//xDisplacement) * xDisplacement 
    beadsHeight = int(height / xDisplacement)
    #make sure we end on an odd row
    if(beadsHeight % 2 == 1):
        height += xDisplacement
        beadsHeight += 1

    print("image = " + str(height) + " x " + str(width))

    tex = np.zeros((height, width, 3), np.uint8) #empty image, just black pixels

    #iterate beads
    for i in range(beadsHeight+1):
        for j in range(beadsWidth+1):
            baseX = (i*xDisplacement) - xDisplacement//2
            baseY = (j*boundBoxLength)
            if(i % 2 == 0):
                baseY -= boundBoxLength//2
            drawBead(baseX, baseY, boundBoxLength, tex, innerRadius, outerRadius, padding)

    cv.imwrite("tex.png", tex) #write file

main()