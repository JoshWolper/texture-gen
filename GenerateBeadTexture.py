import cv2 as cv
import numpy as np
import math

#roughness params
beadRoughness = 0.5

#occlusion params
innerBlendBeginRatio = 0.2
innerBlendEndRatio = 0.3
outerBlendBeginRatio = 0.5
outerBlendEndRatio = 0.8

#flat region (ratio wrt inner circle)
flatRatioBegin = 0.3
flatRatioEnd = 0.5

#bead parameters
beadsWidth = 10 #num beads in width direction
innerRadius = 21 #in pixels
outerRadius = 105
padding = 6
boundBoxLength = (outerRadius + padding) * 2
rin = ((outerRadius-innerRadius) / 2) #radius of tube

def ratioTo256(ratio):
    return math.floor(ratio * 255) 

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

#euqation of semicircle --> y = 2*(0.25 - (x-0.5)^2)^0.5
def computeDisplacement(ratio):
    return 2*math.sqrt((0.25 - pow(ratio - 0.5, 2)))

def drawBead(baseX, baseY, normals, mask, ord):
    cx = baseX + boundBoxLength//2 + padding
    cy = baseY + boundBoxLength//2 + padding
    for i in range(boundBoxLength):
        for j in range(boundBoxLength):
            x = baseX + i
            y = baseY + j
            height, width, depth = normals.shape
            if(x < 0 or y < 0 or x >= height or y >= width):
                continue
            dist = math.sqrt(pow(cx - x, 2) + pow(cy - y, 2))
            if(dist > innerRadius and dist < outerRadius ):
                
                thicknessRatio = ((dist - innerRadius) / (outerRadius-innerRadius)) #ratio through the bead thickness; inner surface = 0, outer surface = 1

                #check if in flat region
                if(thicknessRatio > flatRatioBegin and thicknessRatio < flatRatioEnd):
                   R, G, B = convertNormalToRGB(0,0,1)
                   normals[x, y] = (B, G, R)
                   displacement = 255
                else:
                    #iAngle range = 0 to pi
                    iAngle = thicknessRatio * math.pi

                    #jAngle
                    dirY = x - cx
                    dirX = cy - y #invert sign to flip from pixel coords space
                    length = math.sqrt(dirX*dirX + dirY*dirY)
                    dirX /= length
                    dirY /= length
                    jAngle = math.atan2(dirY, dirX)

                    R, G, B = computeRGB(iAngle, jAngle)
                    normals[x, y] = (B, G, R) #BooGR

                    #compute displacement
                    dispRatio = computeDisplacement(thicknessRatio)
                    displacement = ratioTo256(dispRatio)

                #compute occlusion
                if(thicknessRatio < innerBlendBeginRatio or thicknessRatio > outerBlendEndRatio):
                    occlusion = 0
                elif(thicknessRatio > innerBlendEndRatio and thicknessRatio < outerBlendBeginRatio):
                    occlusion = 255
                elif(thicknessRatio > innerBlendBeginRatio and thicknessRatio < innerBlendEndRatio):
                    ratio = (thicknessRatio - innerBlendBeginRatio) / (innerBlendEndRatio - innerBlendBeginRatio)
                    occlusion = ratioTo256(ratio)
                elif(thicknessRatio > outerBlendBeginRatio and thicknessRatio < outerBlendEndRatio):
                    ratio = (thicknessRatio - outerBlendBeginRatio) / (outerBlendEndRatio - outerBlendBeginRatio)
                    occlusion = ratioTo256(1 - ratio)

                #also write to the mask
                mask[x,y] = (255, 255, 255)
                ord[x,y] = (displacement,ratioTo256(beadRoughness),occlusion)

def main():

    xDisplacement = int(round(math.sqrt(3*pow(outerRadius, 2) + (3 * outerRadius * padding) + 3 * pow(padding, 2))))

    #texture shape parameters
    width = boundBoxLength * beadsWidth
    height = (width//xDisplacement) * xDisplacement 
    beadsHeight = int(height / xDisplacement)
    #make sure we end on an odd row
    if(beadsHeight % 2 == 1):
        height += xDisplacement
        beadsHeight += 1

    print("image = " + str(height) + " x " + str(width))

    R, G, B = convertNormalToRGB(0, 0, 1)
    mask = np.zeros((height, width, 3), np.uint8) #initialize image as all black
    normals = np.full((height, width, 3), (B, G, R)) #initialize image as full of +z normal
    ord = np.full((height, width, 3), (0, 255, 0)) #initialize full - 0 displacemnet, 1 roughness, 0 occlusion

    #iterate beads
    for i in range(beadsHeight+1):
        for j in range(beadsWidth+1):
            baseX = (i*xDisplacement) - xDisplacement//2
            baseY = (j*boundBoxLength)
            if(i % 2 == 0):
                baseY -= boundBoxLength//2
            drawBead(baseX, baseY, normals, mask, ord)

    cv.imwrite("beads_normal.png", normals) #write file
    cv.imwrite("beads_mask.png", mask)
    cv.imwrite("beads_ord.png", ord)

main()