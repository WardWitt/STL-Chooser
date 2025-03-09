import socket
import time
import re
import logging
import configparser

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Network configuration
HOST = config['network']['host']
PORT = int(config['network']['port'])

# Logging configuration
logging.basicConfig(
    level=getattr(logging, config['logging']['level']),
    filename=config['logging']['filename'],
    format=config['logging']['format']
)

logging.info('STL-Chooser startup')

# Silence and program thresholds
SILENCE_THRESHOLD = int(config['silence_thresholds']['silence_threshold'])
PROGRAM_THRESHOLD = int(config['silence_thresholds']['program_threshold'])
SILENCE_DURATION = int(config['silence_thresholds']['silence_duration'])
PROGRAM_DURATION = int(config['silence_thresholds']['program_duration'])

silence_counters = {
    'In1LSilence': 0,
    'In1RSilence': 0,
    'In2LSilence': 0,
    'In2RSilence': 0,
    'In3LSilence': 0,
    'In3RSilence': 0,
    'In4LSilence': 0,
    'In4RSilence': 0,
    'In5LSilence': 0,
    'In5RSilence': 0
}
program_counters = {
    'In1L': 0,
    'In1R': 0,
    'In2L': 0,
    'In2R': 0,
    'In3L': 0,
    'In3R': 0,
    'In4L': 0,
    'In4R': 0,
    'In5L': 0,
    'In5R': 0
}

selectedSource = 1

def update_silence_counters():
    try:
        sock.send(str.encode('MTR ICH\n'))
        time.sleep(1)

        RX = (sock.recv(1024).decode('ascii'))
        meters = re.findall(r'MTR ICH (\d+) PEEK:-?\d+:-?\d+ RMS:(-?\d+):(-?\d+)', RX)
        if len(meters) == 8:
            for i in range(5):
                silence_counters[f'In{i+1}LSilence'] = silence_counters[f'In{i+1}LSilence'] + 1 if int(meters[i][1]) < SILENCE_THRESHOLD else 0
                program_counters[f'In{i+1}L'] = program_counters[f'In{i+1}L'] + 1 if int(meters[i][1]) > PROGRAM_THRESHOLD else 0
                silence_counters[f'In{i+1}RSilence'] = silence_counters[f'In{i+1}RSilence'] + 1 if int(meters[i][2]) < SILENCE_THRESHOLD else 0
                program_counters[f'In{i+1}R'] = program_counters[f'In{i+1}R'] + 1 if int(meters[i][2]) > PROGRAM_THRESHOLD else 0
    except socket.error:
        print("Connection lost. Attempting to reconnect...")
        reconnect()

def src_info():
    sock.send(str.encode('SRC\n'))
    time.sleep(1)

    RX = (sock.recv(1024).decode('ascii'))
    pattern = re.compile(r'SRC (\d+) PSNM:"([^"]+)" .*? RTPA:"([\d.]+)')
    matches = pattern.findall(RX)
    return matches

def dst_info():
    sock.send(str.encode('DST\n'))
    time.sleep(1)

    RX = (sock.recv(1024).decode('ascii'))
    pattern = re.compile(r'DST (\d+) NAME:"([^"]+)" ADDR:"([\d.]+)')
    matches = pattern.findall(RX)
    return matches

def selectIn1():
    global selectedSource
    if selectedSource != 1:
        logging.info('Input 1 selected')
        sock.send(str.encode('LOGIN\nDST 1 ADDR:"239.192.0.1 <Fiber>"\n'))
        sock.send(str.encode('LOGIN\nDST 2 ADDR:"239.192.0.1 <Fiber>"\n'))
    selectedSource = 1
    
def selectIn2():
    global selectedSource
    if selectedSource != 2:
        logging.info('Input 2 selected')
        sock.send(str.encode('LOGIN\nDST 1 ADDR:"239.192.0.2 <Microwave>"\n'))
        sock.send(str.encode('LOGIN\nDST 2 ADDR:"239.192.0.2 <Microwave>"\n'))
    selectedSource = 2

def selectIn3():
    global selectedSource
    if selectedSource != 3:
        logging.info('Input 3 selected')
        sock.send(str.encode('LOGIN\nDST 1 ADDR:"239.192.0.3 <IP>"\n'))
        sock.send(str.encode('LOGIN\nDST 2 ADDR:"239.192.0.3 <IP>"\n'))
    selectedSource = 3

def selectIn4():
    global selectedSource
    if selectedSource != 4:
        logging.info('Input 4 selected')
        sock.send(str.encode('LOGIN\nDST 1 ADDR:"239.192.0.4 <MP3>"\n'))
        sock.send(str.encode('LOGIN\nDST 2 ADDR:"239.192.0.4 <MP3>"\n'))
    selectedSource = 4

def selectIn5():
    global selectedSource
    if selectedSource != 5:
        logging.info('Input 5 selected')    
        sock.send(str.encode('LOGIN\nDST 1 ADDR:"239.192.0.5 <End Times>"\n'))
        sock.send(str.encode('LOGIN\nDST 2 ADDR:"239.192.0.5 <End Times>"\n'))
    selectedSource = 5

def reconnect():
    global sock
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            sock.settimeout(10)
            logging.info("Reconnected to the server.")
            break
        except socket.error:
            print("Failed to reconnect. Retrying in 5 seconds...")
            time.sleep(5)

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.settimeout(10)
except socket.error:
    reconnect()

source_info = src_info()
destination_info = dst_info()

logging.info(destination_info)
logging.info(source_info)

while True:
    try:
        update_silence_counters()
        if(silence_counters['In1LSilence'] > SILENCE_DURATION or silence_counters['In1RSilence'] > SILENCE_DURATION):
            if(silence_counters['In2LSilence'] < 10 and silence_counters['In2RSilence'] < 10):
                selectIn2()
            elif(silence_counters['In3LSilence'] < 10 and silence_counters['In3RSilence'] < 10):
                selectIn3()
            elif(silence_counters['In4LSilence'] < 10 and silence_counters['In4RSilence'] < 10):
                selectIn4()
            elif(silence_counters['In5LSilence'] < 10 and silence_counters['In5RSilence'] < 10):
                selectIn5()
        else:
            if(program_counters['In1L'] > PROGRAM_DURATION and program_counters['In1R'] > PROGRAM_DURATION):
                selectIn1()
    except socket.error:
        logging.info("Connection lost. Attempting to reconnect...")
        reconnect()
