import RPi.GPIO as GPIO
import pygame
from time import sleep
import time
import pvporcupine
import pyaudio
import struct
import subprocess
import foto
import multiprocessing

def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        sleep(0.1)

def get_distance(TRIG,ECHO):
    GPIO.output(TRIG, True)
    sleep(0.00001)
    GPIO.output(TRIG, False)

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    return distance


#DISPLAY
display_process = multiprocessing.Process(target=subprocess.run, args=(["/home/pi/myenv/bin/python","/home/pi/Desktop/robot/display/logo.py"],), kwargs={"check": False})
display_process.start()

#Porcupine Setup
# Replace with your Picovoice access key
ACCESS_KEY = "-"

# Path to your custom wake word .ppn file
WAKE_WORD_PATH = "/home/pi/Desktop/robot/Quieto_es_raspberry-pi_v3_0_0.ppn"

# Path to the Spanish model file
MODEL_PATH = "/home/pi/Desktop/robot/porcupine_params_es.pv"

# Initialize Porcupine with the custom wake word and Spanish model file
porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=[WAKE_WORD_PATH],
    model_path=MODEL_PATH
)

# Initialize PyAudio
pa = pyaudio.PyAudio()

# Open audio stream
stream = pa.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=porcupine.sample_rate,
    input=True,
    frames_per_buffer=porcupine.frame_length
)

#Ultrasonic sensors
"""
US_front = DistanceSensor(echo=23, trigger=24)
US_back = DistanceSensor(echo=25, trigger=8)
"""
# Pin Definitions
#US_Front
TF=24
EF=23
#US_Front
TB=8
EB=25
#Motor R
E1=12 #PWM
M1=5 #PDOut
#Motor L
E2=19 #PWM
M2=6 #PDOut
#IR sensors
IR_front = 4
IR_back = 26
#Relays
R1=17
R2=27
R3=22
#Start/Stop Button
#B=16

# Setup GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM numbering
#Ultrasound
GPIO.setup(TF, GPIO.OUT)
GPIO.setup(TB, GPIO.OUT)
GPIO.setup(EF, GPIO.IN)
GPIO.setup(EB, GPIO.IN)
#Motor L
GPIO.setup(E1, GPIO.OUT)
GPIO.setup(M1, GPIO.OUT)
#Motor R
GPIO.setup(E2, GPIO.OUT)
GPIO.setup(M2, GPIO.OUT)
#IR sensors
GPIO.setup(IR_front, GPIO.IN)
GPIO.setup(IR_back, GPIO.IN)
#Relay
GPIO.setup(R1, GPIO.OUT)
GPIO.setup(R2, GPIO.OUT)
GPIO.setup(R3, GPIO.OUT)
#Start/Stop Button
#GPIO.setup(B, GPIO.IN)

motorR = GPIO.PWM(E1, 1000)  # 1 kHz frequency
motorL = GPIO.PWM(E2, 1000)  # 1 kHz frequency
motorR.start(0)
motorL.start(0)

direction = -1
GPIO.output(M1, GPIO.LOW) #Sentit  Agulles del rellotge
GPIO.output(M2, GPIO.LOW) #Sentit  Agulles del rellotge

speed=100

motorR.ChangeDutyCycle(speed)
motorL.ChangeDutyCycle(speed)

run=True


while run:

    #RUNNING FRONT
    if (direction == 1):
        
        if(GPIO.input(IR_front)!=1):#El sensor de davant torna 0, no hi ha terra
            motorR.ChangeDutyCycle(0)
            motorL.ChangeDutyCycle(0)
            sleep(0.5)
            GPIO.output(M1, GPIO.LOW) #Sentit Contrari Agulles del rellotge
            GPIO.output(M2, GPIO.LOW) #Sentit Contrari Agulles del rellotge
            motorR.ChangeDutyCycle(speed)
            motorL.ChangeDutyCycle(speed) 
            direction = -1
        
        if(get_distance(TF,EF)<25):
            print("Objecte davant")
            motorR.ChangeDutyCycle(0)
            motorL.ChangeDutyCycle(0)
            sleep(0.5)
            play_audio('/home/pi/Desktop/robot/audios/bloqueo_delantero.mp3')
            sleep(1)
            motorR.ChangeDutyCycle(speed)
            motorL.ChangeDutyCycle(speed) 
            
    #RUNNING BACK
    elif (direction == -1):
        
        if(GPIO.input(IR_back)!=1):#El sensor de darrera torna 0, no hi ha terra
            motorR.ChangeDutyCycle(0)
            motorL.ChangeDutyCycle(0)
            sleep(0.5)
            GPIO.output(M1, GPIO.HIGH) #Sentit Contrari Agulles del rellotge
            GPIO.output(M2, GPIO.HIGH) #Sentit Contrari Agulles del rellotge
            motorR.ChangeDutyCycle(speed)
            motorL.ChangeDutyCycle(speed)
            direction = 1
        if(get_distance(TB,EB)<25):
            print("Objecte davant")
            motorR.ChangeDutyCycle(0)
            motorL.ChangeDutyCycle(0)
            sleep(0.5)
            play_audio('/home/pi/Desktop/robot/audios/bloqueo_trasero.mp3')
            sleep(1)
            motorR.ChangeDutyCycle(speed)
            motorL.ChangeDutyCycle(speed) 

    #AUDIO & FACE RECOGNITION
    pcm = stream.read(porcupine.frame_length)
    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
    keyword_index = porcupine.process(pcm)
    if keyword_index >= 0:
        motorR.ChangeDutyCycle(0)
        motorL.ChangeDutyCycle(0)
        print("Wake word detected!")
        sleep(1)
        foto.play_audio("/home/pi/Desktop/robot/audios/camara1.mp3")
        sleep(1)
        valvula = foto.identify()
        if(valvula=='1'):
            print(1)
            GPIO.output(R2,1)
            sleep(30)
            GPIO.output(R2,0)
        elif(valvula=='2'):
            print(2)
            GPIO.output(R1,1)
            sleep(30)
            GPIO.output(R1,0)
        elif(valvula=='3'):
            print(3)
            GPIO.output(R3,1)
            sleep(30)
            GPIO.output(R3,0)
        elif(valvula=='mezcla'):
            print('mezcla')
            GPIO.output(R1,1)
            GPIO.output(R2,1)
            GPIO.output(R3,1)
            sleep(30)
            GPIO.output(R1,0)
            GPIO.output(R2,0)
            GPIO.output(R3,0)
    

    
GPIO.cleanup()
stream.stop_stream()
stream.close()
pa.terminate()
porcupine.delete()
