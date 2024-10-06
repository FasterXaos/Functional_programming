import csv
import cv2
import multiprocessing
import numpy
import os
import tkinter as tk
from tkinter import filedialog, messagebox, Text

objectColors = {
    "Star": (255, 0, 0),
    "Planet": (0, 255, 0),
    "Galaxy": (0, 0, 255),
    "Unknown Object": (255, 255, 0)
}

def analyzeImagePart(arguments):
    imagePart, partIndex, imageName, offsetX, offsetY, outputDirectory = arguments
    
    grayImage = applyCLAHE(imagePart) 
    blurredImage = cv2.GaussianBlur(grayImage, (5, 5), 0)
    _, binaryImage = cv2.threshold(blurredImage, 140, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binaryImage, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    objectsData = []
    
    for contour in contours:
        contourArea = cv2.contourArea(contour)
        x, y, contourWidth, contourHeight = cv2.boundingRect(contour)
        centerX = x + contourWidth // 2 + offsetX
        centerY = y + contourHeight // 2 + offsetY
        
        brightness = numpy.sum(grayImage[y:y + contourHeight, x:x + contourWidth])
        objectType = classifyObject(contourArea, brightness)

        color = objectColors.get(objectType, (0, 255, 255))
        cv2.rectangle(imagePart, (x, y), (x + contourWidth, y + contourHeight), color, 2)
        cv2.putText(imagePart, objectType, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        objectsData.append({
            "imageName": imageName,
            "partIndex": partIndex,
            "coordinates": (centerX, centerY),
            "brightness": brightness,
            "area": contourArea,
            "type": objectType,
            "size": contourWidth * contourHeight
        })

    partImagePath = os.path.join(outputDirectory, f"{imageName}_part{partIndex}.png")
    cv2.imwrite(partImagePath, imagePart)

    #print(f"Finished analyzing part {partIndex} of image {imageName}")
    return objectsData

def applyCLAHE(image):
    grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalizedImage = clahe.apply(grayImage)
    
    return equalizedImage

def classifyObject(area, brightness):
    if area < 100 and brightness > 700:
        return "Star"
    elif area < 1000 and brightness > 300:
        return "Planet"
    elif area >= 1000 and brightness > 10000:
        return "Galaxy"
    else:
        return "Unknown Object"

def processAllImages(inputDirectory, outputDirectory, outputCSVPath, statusText):
    allResults = []

    if not os.path.exists(inputDirectory):
        statusText.insert(tk.END, "Input directory does not exist!\n")
        return
    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)

    for imageName in os.listdir(inputDirectory):
        imagePath = os.path.join(inputDirectory, imageName)
        if imagePath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            statusText.insert(tk.END, f"Processing {imageName}...\n")
            statusText.update_idletasks()
            objectsData = processImage(imagePath, outputDirectory)
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

    statusText.insert(tk.END, f"Analysis complete. Results saved to {outputCSVPath}\n")

def processImage(imagePath, outputDirectory):
    image = cv2.imread(imagePath)
    imageName = os.path.basename(imagePath)
    
    imageParts = splitImage(image, 500)
    arguments = [(part, partIndex, imageName, offsetX, offsetY, outputDirectory) 
                 for part, offsetX, offsetY, partIndex in imageParts]
    
    with multiprocessing.Pool(processes=16) as processPool:
        results = processPool.map(analyzeImagePart, arguments)

    allObjectsData = []
    for objectData in results:
        allObjectsData.extend(objectData)

    return allObjectsData

def selectOutputDirectory():
    outputDirectory = filedialog.askdirectory()
    outputDirEntry.delete(0, tk.END)
    outputDirEntry.insert(0, outputDirectory)
    
def selectInputDirectory():
    inputDirectory = filedialog.askdirectory()
    inputDirEntry.delete(0, tk.END)
    inputDirEntry.insert(0, inputDirectory)

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

def startProcessing():
    inputDirectory = inputDirEntry.get()
    outputDirectory = outputDirEntry.get()
    outputCSVPath = os.path.join(outputDirectory, 'astroObjectsStatistics.csv')
    
    if not inputDirectory or not outputDirectory:
        messagebox.showerror("Error", "Please select both input and output directories.")
        return

    statusText.delete(1.0, tk.END)
    processAllImages(inputDirectory, outputDirectory, outputCSVPath, statusText)

if __name__ == "__main__":
    app = tk.Tk()
    app.title("Astronomical Object Analyzer")

    app.grid_columnconfigure(1, weight=1)
    app.grid_rowconfigure(3, weight=1)

    inputDirLabel = tk.Label(app, text="Input Directory:")
    inputDirLabel.grid(row=0, column=0, padx=10, pady=5)
    inputDirEntry = tk.Entry(app, width=50)
    inputDirEntry.grid(row=0, column=1, sticky="we")
    inputDirButton = tk.Button(app, text="Browse", command=selectInputDirectory)
    inputDirButton.grid(row=0, column=2, padx=10, pady=5)

    outputDirLabel = tk.Label(app, text="Output Directory:")
    outputDirLabel.grid(row=1, column=0, padx=10, pady=5)
    outputDirEntry = tk.Entry(app, width=50)
    outputDirEntry.grid(row=1, column=1, sticky="we")
    outputDirButton = tk.Button(app, text="Browse", command=selectOutputDirectory)
    outputDirButton.grid(row=1, column=2, padx=10, pady=5)

    processButton = tk.Button(app, text="Process Images", command=startProcessing)
    processButton.grid(row=2, column=1, pady=5)

    statusText = Text(app, height=10, width=70)
    statusText.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    app.mainloop()
