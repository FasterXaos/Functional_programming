import csv
import cv2
import multiprocessing as multiprocessing
import numpy as numpy
import os

def analyzeImagePart(arguments):
    imagePart, partIndex, imageName, offsetX, offsetY = arguments
    
    grayImage = cv2.cvtColor(imagePart, cv2.COLOR_BGR2GRAY)
    blurredImage = cv2.GaussianBlur(grayImage, (5, 5), 0)
    _, binaryImage = cv2.threshold(blurredImage, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binaryImage, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    objectsData = []
    
    for contour in contours:
        contourArea = cv2.contourArea(contour)
        x, y, contourWidth, contourHeight = cv2.boundingRect(contour)
        centerX = x + contourWidth // 2 + offsetX
        centerY = y + contourHeight // 2 + offsetY
        
        brightness = numpy.sum(grayImage[y:y + contourHeight, x:x + contourWidth])
        objectType = classifyObject(contourArea, brightness)
        
        objectsData.append({
            "imageName": imageName,
            "partIndex": partIndex,
            "coordinates": (centerX, centerY),
            "brightness": brightness,
            "area": contourArea,
            "type": objectType,
            "size": contourWidth * contourHeight
        })

    print(f"Finished analyzing part {partIndex} of image {imageName}")
    return objectsData

def classifyObject(area, brightness):
    if area < 100 and brightness > 1000:
        return "Star"
    elif area < 1000 and brightness > 500:
        return "Planet"
    elif area >= 1000 and brightness > 10000:
        return "Galaxy"
    else:
        return "Unknown Object"

def processAllImages(inputDirectory, outputCSVPath):
    allResults = []

    for imageName in os.listdir(inputDirectory):
        imagePath = os.path.join(inputDirectory, imageName)
        if imagePath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            print(f"Processing {imageName}...")
            objectsData = processImage(imagePath)
            allResults.extend(objectsData)

    with open(outputCSVPath, mode='w', newline='') as csvFile:
        fieldnames = ['imageName', 'partIndex', 'coordinates', 'brightness', 'area', 'type', 'size']
        csvWriter = csv.DictWriter(csvFile, fieldnames=fieldnames)
        csvWriter.writeheader()
        
        for objectData in allResults:
            csvWriter.writerow({
                'imageName': objectData['imageName'],
                'partIndex': objectData['partIndex'],
                'coordinates': objectData['coordinates'],
                'brightness': objectData['brightness'],
                'area': objectData['area'],
                'type': objectData['type'],
                'size': objectData['size']
            })

    print(f"Analysis complete. Results saved to {outputCSVPath}")

def processImage(imagePath):
    image = cv2.imread(imagePath)
    imageName = os.path.basename(imagePath)
    
    imageParts = splitImage(image, 2000)
    arguments = [(part, partIndex, imageName, offsetX, offsetY) 
                 for part, offsetX, offsetY, partIndex in imageParts]
    
    with multiprocessing.Pool(processes=16) as processPool:
        results = processPool.map(analyzeImagePart, arguments)

    allObjectsData = []
    for objectData in results:
        allObjectsData.extend(objectData)

    return allObjectsData

def splitImage(image, partSize=1000):
    imageHeight, imageWidth, _ = image.shape
    imageParts = []
    
    partIndex = 0
    for offsetY in range(0, imageHeight, partSize):
        for offsetX in range(0, imageWidth, partSize):
            part = image[offsetY:offsetY + partSize, offsetX:offsetX + partSize]
            imageParts.append((part, offsetX, offsetY, partIndex))
            partIndex += 1
    
    return imageParts

if __name__ == "__main__":
    inputDirectory = 'images'
    outputCSVPath = 'astroObjectsStatistics.csv'

    processAllImages(inputDirectory, outputCSVPath)
