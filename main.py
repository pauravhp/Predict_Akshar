# Sketching code adapted from -
# https://www.thepythoncode.com/code/make-a-drawing-program-with-python
# https://www.thepythoncode.com/article/make-a-drawing-program-with-python

# Imports
import sys

import pygame
import ctypes

import tensorflow as tf
import numpy as np

import threading

import bson

from PIL import Image

from datetime import datetime

from pymongo import MongoClient

from dotenv import load_dotenv
import os

load_dotenv()

# Connecting to MongoDB
mongodb_url = os.getenv("MONGODB_URL")
client = MongoClient(mongodb_url)
db = client["Test"]  # Database name
collection = db["PredLogs"]  # Collection name

# Lock for MongoDB access, to avoid any sort of race conditions or errors with MongoDB access
mongo_lock = threading.Lock()

# Pygame Configuration
pygame.init()
fps = 300
fpsClock = pygame.time.Clock()
width, height = 640, 480
screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

pygame.font.init()
font = pygame.font.SysFont("Arial", 16)

# Variables

# The Buttons will append themself to this list
objects = []

# Brush color
drawColor = [255, 255, 255]

# Brush size
brushSize = 10
brushSizeSteps = 1

# Drawing Area Size, x10 the size of (32,32)
canvasSize = [320, 320]

# Prediction made by model
prediction_msg = ""


# Button Class
class Button:
    def __init__(
        self,
        x,
        y,
        width,
        height,
        buttonText="Button",
        onclickFunction=None,
        onePress=False,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onclickFunction = onclickFunction
        self.onePress = onePress

        self.fillColors = {
            "normal": "#ffffff",
            "hover": "#666666",
            "pressed": "#333333",
        }

        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.buttonSurf = font.render(buttonText, True, (20, 20, 20))

        self.alreadyPressed = False

        objects.append(self)

    def process(self):
        mousePos = pygame.mouse.get_pos()

        self.buttonSurface.fill(self.fillColors["normal"])
        if self.buttonRect.collidepoint(mousePos):
            self.buttonSurface.fill(self.fillColors["hover"])

            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.buttonSurface.fill(self.fillColors["pressed"])

                if self.onePress:
                    self.onclickFunction()

                elif not self.alreadyPressed:
                    self.onclickFunction()
                    self.alreadyPressed = True

            else:
                self.alreadyPressed = False

        self.buttonSurface.blit(
            self.buttonSurf,
            [
                self.buttonRect.width / 2 - self.buttonSurf.get_rect().width / 2,
                self.buttonRect.height / 2 - self.buttonSurf.get_rect().height / 2,
            ],
        )
        screen.blit(self.buttonSurface, self.buttonRect)


# Handler Functions

# Function to insert data into MongoDB

# Document contents - date, time, prediction image, prediction made
# Asynchronous Programming
#   Create a thread that calls the insert data upon creation (check limits for argument data)
#   Mutex Locks when inserting
# insert_data is called when prediction is made

# Further functionality
#    If its the same image, no new document is added, the prediction is updated with the newest one
#    or appeneded to
#        Maybe create a userId for every canvas image created, and crosscheck to create new document


def insert_data(datetime, pred_img, pred):
    # Accquiring mutex lock
    with mongo_lock:
        # Convert pred_img to Binary BSON
        binary_img = bson.Binary(pred_img)

        document = {
            "Date": datetime,
            "Predicted Image": binary_img,
            "Prediction made": pred,
        }
        result = collection.insert_one(document)
        inserted_id = result.inserted_id
        print(f"{inserted_id} - Prediction logged successfully!")


# Function to handle database insertions asynchronously via threads
def handle_database_insertion(datetime, pred_img, pred):
    thread = threading.Thread(
        target=insert_data,
        args=(
            datetime,
            pred_img,
            pred,
        ),
    )
    thread.start()


# Save the surface to the Disk
def save():
    pygame.image.save(canvas, "canvas.png")


def clear():
    canvas.fill((0, 0, 0))


def predict():
    save()

    model = tf.keras.models.load_model("hindi_letter_model.h5")

    image = Image.open("canvas.png")
    image = image.convert("RGB")

    target_size = (32, 32)
    image.thumbnail(target_size, Image.ANTIALIAS)
    canvas = Image.new("RGB", target_size, (255, 255, 255))

    offset = (
        (target_size[0] - image.size[0]) // 2,
        (target_size[1] - image.size[1]) // 2,
    )
    canvas.paste(image, offset)

    array = np.array(canvas)
    array = np.expand_dims(array, axis=0)

    prediction = model.predict(array)
    answer = np.argmax(prediction)

    ans_li = [
        "yna",
        "taamatar",
        "thaa",
        "daa",
        "dhaa",
        "adna",
        "tabala",
        "tha",
        "da",
        "dha",
        "ka",
        "na",
        "pa",
        "pha",
        "ba",
        "bha",
        "ma",
        "yaw",
        "ra",
        "la",
        "waw",
        "kha",
        "motosaw",
        "petchiryakha",
        "patalosaw",
        "ha",
        "chhya",
        "tra",
        "gya",
        "ga",
        "gha",
        "kna",
        "cha",
        "chha",
        "ja",
        "jha",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
    ]
    global prediction_msg
    prediction_msg = "Prediction: " + ans_li[answer]
    print(prediction_msg)

    current_datetime = datetime.now()
    # Format the current date and time
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    with open("canvas.png", "rb") as file:
        pred_img = file.read()

    handle_database_insertion(formatted_datetime, pred_img, ans_li[answer])


# Button Variables.
buttonWidth = 120
buttonHeight = 35

# Buttons and their respective functions.
buttons = [
    ["Clear", clear],
    ["Predict", predict],
]

# Making the buttons
for index, buttonName in enumerate(buttons):
    Button(
        index * (buttonWidth + 10) + 10,
        10,
        buttonWidth,
        buttonHeight,
        buttonName[0],
        buttonName[1],
    )

# Canvas
canvas = pygame.Surface(canvasSize)
canvas.fill((0, 0, 0))


# Game loop.
while True:
    screen.fill((30, 30, 30))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Drawing the Buttons
    for object in objects:
        object.process()

    # Draw the Canvas at the center of the screen
    x, y = screen.get_size()
    screen.blit(canvas, [x / 2 - canvasSize[0] / 2, y / 2 - canvasSize[1] / 2])

    # Drawing with the mouse
    if pygame.mouse.get_pressed()[0]:
        mx, my = pygame.mouse.get_pos()

        # Calculate Position on the Canvas
        dx = mx - x / 2 + canvasSize[0] / 2
        dy = my - y / 2 + canvasSize[1] / 2

        pygame.draw.circle(
            canvas,
            drawColor,
            [dx, dy],
            brushSize,
        )

    # Reference Dot
    pygame.draw.circle(
        screen,
        drawColor,
        [100, 100],
        brushSize,
    )

    # Displaying Model's Prediction
    text_surface = font.render(prediction_msg, True, (255, 255, 255))
    screen.blit(text_surface, (10, height - 30))

    pygame.display.flip()
    fpsClock.tick(fps)
