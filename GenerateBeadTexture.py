import cv2 as cv
import numpy as np
import math

def convertNormalToRGB(nx, ny, nz):
    assert(nx >= -1 and nx <= 1 and ny >= -1 and ny <= 1 and nz >= -1 and nz <= 1)
    R = 0
    G = 0
    B = 0
    if(nx <= 0):
        R = (abs((-1 - nx) / 2)) * 255
    else:
        R = ((nx + 1) / 2) * 255

    if(ny <= 0):
        G = (abs((-1 - ny) / 2)) * 255
    else:
        G = ((ny + 1) / 2) * 255

    if(nz <= 0):
        B = (abs((-1 - nz) / 2)) * 255
    else:
        B = ((nz + 1) / 2) * 255
    
    return R, G, B

# torus normals adapted from https://www.cs.ucdavis.edu/~amenta/s06/findnorm.pdf
def computeRGB(iAngle, jAngle):

    #tangent vector wrt bigger circle
    tx = -math.sin(jAngle)
    ty = math.cos(jAngle)
    tz = 0

    #tangent vector wrt smaller crcle
    sx = math.cos(jAngle) * -math.sin(iAngle)
    sy = math.sin(jAngle)*-math.sin(iAngle)
    sz = math.cos(iAngle)

    #normal is cross product
    nx = ty*sz - tz*sy
    ny = tz*sx - tx*sz
    nz = tx*sy - ty*sx
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    nx /= length
    ny /= length
    nz /= length

    R, G, B = convertNormalToRGB(nx, ny, nz)
    
    return R, G, B

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

                #iAngle range = 0 to pi
                iAngle = ((dist - r1) / (r2 - r1)) * math.pi

                #jAngle
                dirY = x - cx
                dirX = cy - y #invert sign to flip from pixel coords space
                length = math.sqrt(dirX*dirX + dirY*dirY)
                dirX /= length
                dirY /= length
                jAngle = math.atan2(dirY, dirX)

                R, G, B = computeRGB(iAngle, jAngle)
                img[x, y] = (B, G, R) #BooGR

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

    R, G, B = convertNormalToRGB(0, 0, 1)
    tex = np.full((height, width, 3), (B, G, R)) #initialize image as 

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