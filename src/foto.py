import numpy as np
import cv2
import pyaudio
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from skimage.feature import hog
from time import sleep
import os
import subprocess
import pygame
import warnings
import random
import pvleopard as pv
import wave
warnings.filterwarnings("ignore")

def picture(save_path):
    # Command to capture an image using libcamera-still
    command = ["libcamera-still", "-o", save_path]

    try:
        # Execute the command
        subprocess.run(command, check=True)
        print(f"Image captured and saved to {save_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error capturing image: {e}")

def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        sleep(0.1)

def record_audio(file_path, duration=5, chunk_size=1024, sample_format=pyaudio.paInt16, channels=1, rate=44100):
    """Record audio from the microphone and save it to a WAV file."""
    
    # Initialize PyAudio
    audio = pyaudio.PyAudio()
    
    # Open audio stream
    stream = audio.open(format=sample_format,
                        channels=channels,
                        rate=rate,
                        frames_per_buffer=chunk_size,
                        input=True)
    
    print("Recording...")
    
    frames = []
    
    # Record audio in chunks
    for _ in range(int(rate / chunk_size * duration)):
        data = stream.read(chunk_size)
        frames.append(data)
    
    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    
    # Terminate PyAudio
    audio.terminate()
    
    print("Finished recording.")
    
    # Save the recorded audio to a WAV file
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(sample_format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))

# Replace these paths with the actual paths on your system
ACCESS_KEY = '-'
MODEL_PATH_SPEECH = "/home/pi/Desktop/robot/robot-leopard.pv"

def recognize_speech():
    # Initialize Leopard
    leopard = pv.create(
        access_key=ACCESS_KEY,
        model_path=MODEL_PATH_SPEECH
    )

    file_path = "/home/pi/Desktop/robot/audios/recorded_audio.wav"
    record_audio(file_path, duration=3)
    
    transcript, words = leopard.process_file(file_path)
    leopard.delete()

    return transcript

def get_target(num):
    path = os.path.join("/home/pi/Desktop/robot/targets", num)
    print(path)
    with open(path + '/target.txt', 'r') as file:
        contenido = file.read()
    return contenido

def load_dataset(dataset_path):
    dataset = []
    num_folders = sorted(os.listdir(dataset_path), key=lambda x: int(x))
    
    for num_folder in num_folders:
        num_folder_path = os.path.join(dataset_path, num_folder)
        for img_name in os.listdir(num_folder_path):
            img_path = os.path.join(num_folder_path, img_name)
            img = cv2.imread(img_path)
            flipped = cv2.flip(img,1)
            flipped = np.array(flipped)
            flipped = cv2.cvtColor(flipped, cv2.COLOR_RGB2GRAY)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
            random_value = random.uniform(1.2, 1.5)
            increase = np.ones((64, 64)) * random_value
            random_value = random.uniform(0.5, 0.8)
            decrease = np.ones((64, 64)) * 0.65
            
            img = img/255.0
            dataset.append((img, num_folder))
           
            flipped = flipped/255.0
            dataset.append((flipped, num_folder))
            
            bright_img = np.clip(img * increase, 0, 1)
            dataset.append((bright_img, num_folder))
            
            bright_flipped = np.clip(flipped * increase, 0, 1)
            dataset.append((bright_flipped, num_folder))
            
            bright_img2 = np.clip(img * decrease, 0, 1)
            dataset.append((bright_img2, num_folder))
            
            bright_flipped2 = np.clip(flipped * decrease, 0, 1)
            dataset.append((bright_flipped2, num_folder))
            
            random_value = random.uniform(0.02, 0.033)
            noise_img1 = img + np.random.normal(0, random_value, img.shape)
            noise_img1 = np.clip(noise_img1, 0, 1)
            dataset.append((noise_img1, num_folder))

            noise_img2 = flipped + np.random.normal(0, random_value, flipped.shape)
            noise_img2 = np.clip(noise_img2, 0, 1)
            dataset.append((noise_img2, num_folder))
            
            blur_img1 = cv2.GaussianBlur(img, (5, 5), 0)
            dataset.append((blur_img1, num_folder))
            blur_img2 = cv2.GaussianBlur(flipped, (5, 5), 0)
            dataset.append((blur_img2, num_folder))
           
    return dataset

def get_next_image_name(folder_path):
    # Find the highest numbered image file in the dataset folder
    existing_images = [f for f in os.listdir(folder_path) if f.startswith("img") and f.endswith(".png")]
    if not existing_images:
        return "img0.png"  # If no images found, start with img0.jpg
    else:
        highest_number = max([int(img.split("img")[1].split(".png")[0]) for img in existing_images])
        next_number = highest_number + 1
        return "img{}.png".format(next_number)

def capture_img(folder_number,save=True):
    
    dataset_folder = "/home/pi/Desktop/robot/dataset"
    
    picture("/home/pi/Desktop/robot/test.jpg")
    image = cv2.imread("/home/pi/Desktop/robot/test.jpg")

    grayscale_frame = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(grayscale_frame, scaleFactor=1.1, minNeighbors=5)
    if len(faces) > 0:
        (x, y, w, h) = faces[0]  # Assuming only one face is detected, you can modify this if needed
        face_image = grayscale_frame[y:y+h, x:x+w]
        grayscale_frame = cv2.resize(face_image, (64, 64))
        
        if save:
            folder_path = os.path.join(dataset_folder, str(folder_number))
            # Check if the folder exists, if not, create it
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            # Save the grayscale image in the dataset folder
            next_img_name = get_next_image_name(folder_path)  # You need to define get_next_image_name() function
            img_path = os.path.join(folder_path, next_img_name)
            cv2.imwrite(img_path, grayscale_frame)
            
        # Release the webcam
        
        print("Image captured, resized to 64x64 pixels, converted to grayscale, and normalized")
        
        return grayscale_frame
    else:
        print("No face detected")
        return None
    
def set_target(folder_number, target, save=True):

    dataset_folder = "/home/pi/Desktop/robot/targets"
        
    if save:
        folder_path = os.path.join(dataset_folder, str(folder_number))
        folder_path = os.path.join(folder_path)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        with open(folder_path+'/target.txt', "w") as file:
            file.write(str(target))
        

def identify():
    dataset_path = "/home/pi/Desktop/robot/dataset"
    data = load_dataset(dataset_path)
    if(len(data)!=0):
        print("Wait")
        X_data=[]
        for img in data:
            X_data.append(img[0])
        X_data=np.array(X_data)
        y_data=[]
        for target in data:
            y_data.append(target[1])
        y_data=np.array(y_data)
        
        X_hog=[]
        for img in X_data:
            fd, hog_image = hog(img, orientations=8, pixels_per_cell=(16, 16), cells_per_block=(1, 1), visualize=True, channel_axis=None)
            X_hog.append(hog_image)
        X_hog=np.array(X_hog)
    
        # Reshape images
        n_samples, height, width = X_hog.shape
        X_hog = np.reshape(X_hog, (n_samples, height * width))
    
        # Apply PCA
        pca = PCA()  # Choose number of components as per requirement
        pca.fit(X_hog)
        
        component=100
        
        eigenfaces = pca.components_[:component]
    
        threshold = 0.35
        
        weights = eigenfaces @ (X_hog - pca.mean_).T
        play_audio("/home/pi/Desktop/robot/audios/3.mp3")
        sleep(1)
        play_audio("/home/pi/Desktop/robot/audios/2.mp3")
        sleep(1)
        play_audio("/home/pi/Desktop/robot/audios/1.mp3")
        sleep(1)
        
        picture("/home/pi/Desktop/robot/test.jpg")
        image = cv2.imread("/home/pi/Desktop/robot/test.jpg")
        
        grayscale_frame = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)   
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(grayscale_frame, scaleFactor=1.1, minNeighbors=5)
        
        if len(faces) > 0:
            (x, y, w, h) = faces[0]  # Assuming only one face is detected, you can modify this if needed
            face_image = grayscale_frame[y:y+h, x:x+w]
            grayscale_frame = cv2.resize(face_image, (64, 64))
            fd, hog_target = hog(grayscale_frame, orientations=8, pixels_per_cell=(16, 16), cells_per_block=(1, 1), visualize=True, channel_axis=None)
            hog_target = hog_target/255
            img_weight = eigenfaces @ (hog_target.reshape(1, -1) - pca.mean_).T
    
            euclidean_distance = np.linalg.norm(weights - img_weight, axis=0)
            closest_index = np.argsort(euclidean_distance)[0]
            print(euclidean_distance[closest_index])
            if euclidean_distance[closest_index] < threshold:
                neighbor_label = y_data[closest_index]
    
                return get_target(neighbor_label)

            else:
                play_audio("/home/pi/Desktop/robot/audios/ningu_base_de_dades.mp3")
                play_audio("/home/pi/Desktop/robot/audios/primera_imagen.mp3")
                capture_img(1)
                play_audio("/home/pi/Desktop/robot/audios/segunda_imagen.mp3")
                capture_img(1)
                play_audio("/home/pi/Desktop/robot/audios/tercera_imagen.mp3")
                capture_img(1)
                play_audio("/home/pi/Desktop/robot/audios/cuarta_imagen.mp3")
                capture_img(1)
                
                play_audio("/home/pi/Desktop/robot/audios/que_desea_tomar.mp3")
                x=True
                while(x):
                    x=False
                    text=recognize_speech()
                    print(text)
                    if(text.lower()=='uno'):
                        set_target(1, '1')
                        return '1'
                    elif(text.lower()=='dos'):
                        set_target(1, '2')
                        return '2'
                    elif(text.lower()=='tres'):
                        set_target(1, '3')
                        return '3'
                    elif(text.lower()=='mezcla'):
                        set_target(1, 'mezcla')
                        return 'mezcla'
                    else:
                        play_audio("/home/pi/Desktop/robot/audios/error_bo.mp3")
                        x=True

        else:
            print("No face detected.")
            play_audio("/home/pi/Desktop/robot/audios/no_cara.mp3")
            x=True
            while(x):
                x=False
                text=recognize_speech()
                print(text)
                if(text.lower()=='uno'):
                    return '1'
                elif(text.lower()=='dos'):
                    return '2'
                elif(text.lower()=='tres'):
                    return '3'
                elif(text.lower()=='mezcla'):
                    return 'mezcla'
                else:
                    play_audio("/home/pi/Desktop/robot/audios/error_bo.mp3")
                    x=True
    
    else:
        
        play_audio("/home/pi/Desktop/robot/audios/ningu_base_de_dades.mp3")
        play_audio("/home/pi/Desktop/robot/audios/primera_imagen.mp3")
        capture_img(1)
        play_audio("/home/pi/Desktop/robot/audios/segunda_imagen.mp3")
        capture_img(1)
        play_audio("/home/pi/Desktop/robot/audios/tercera_imagen.mp3")
        capture_img(1)
        play_audio("/home/pi/Desktop/robot/audios/cuarta_imagen.mp3")
        capture_img(1)        
        play_audio("/home/pi/Desktop/robot/audios/que_desea_tomar.mp3")
        x=True
        while(x):
            x=False
            text=recognize_speech()
            print(text)
            if(text.lower()=='uno'):
                set_target(1, '1')
                return '1'
            elif(text.lower()=='dos'):
                set_target(1, '2')
                return '2'
            elif(text.lower()=='tres'):
                set_target(1, '3')
                return '3'
            elif(text.lower()=='mezcla'):
                set_target(1, 'mezcla')
                return 'mezcla'
            else:
                play_audio("/home/pi/Desktop/robot/audios/error_bo.mp3")
                x=True
