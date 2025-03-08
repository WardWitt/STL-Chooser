import socket
import time
import re
import logging

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

logging.basicConfig(
    level = logging.INFO,
    filename="STL-Chooser.log",
    format="%(name)s - %(levelname)s - %(message)s - %(asctime)s",
)

logging.info('STL-Chooser startup')

def update_silence_counters():
    try:
        sock.send(str.encode('MTR ICH\n'))
        time.sleep(1)

        RX = (sock.recv(1024).decode('ascii'))
        # Regular expression to find RMS values tagged with ICH and their channel numbers
        meters = re.findall(r'MTR ICH (\d+) PEEK:-?\d+:-?\d+ RMS:(-?\d+):(-?\d+)', RX)
        # make sure we got a complete set of meters, sometimes the return gets corrupted with status updates
        if len(meters) == 8:
            for i in range(5):
                silence_counters[f'In{i+1}LSilence'] = silence_counters[f'In{i+1}LSilence'] + 1 if int(meters[i][1]) < -500 else 0
                program_counters[f'In{i+1}L'] = program_counters[f'In{i+1}L'] + 1 if int(meters[i][1]) > -1000 else 0
                silence_counters[f'In{i+1}RSilence'] = silence_counters[f'In{i+1}RSilence'] + 1 if int(meters[i][2]) < -500 else 0
                program_counters[f'In{i+1}R'] = program_counters[f'In{i+1}R'] + 1 if int(meters[i][2]) > -1000 else 0
            # print(silence_counters)
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
            sock.connect(('10.0.0.42', 93))
            sock.settimeout(10)
            logging.info("Reconnected to the server.")
            break
        except socket.error:
            print("Failed to reconnect. Retrying in 5 seconds...")
            time.sleep(5)

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('10.0.0.42', 93))
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
        if(silence_counters['In1LSilence'] > 30 or silence_counters['In1RSilence'] > 30):
            # print(source_info[0][1] + ' has been silent for ' + str(silence_counters['In1LSilence']) + ' seconds')
            if(silence_counters['In2LSilence'] < 10 and silence_counters['In2RSilence'] < 10):
                selectIn2()
            elif(silence_counters['In3LSilence'] < 10 and silence_counters['In3RSilence'] < 10):
                selectIn3()
            elif(silence_counters['In4LSilence'] < 10 and silence_counters['In4RSilence'] < 10):
                selectIn4()
            elif(silence_counters['In5LSilence'] < 10 and silence_counters['In5RSilence'] < 10):
                selectIn5()
        else:
            if(program_counters['In1L'] > 10 and program_counters['In1R'] > 10):
                selectIn1()
            
        # if(silence_counters['In2LSilence'] > 30 or silence_counters['In2RSilence'] > 30):
            # print(source_info[1][1] + ' has been silent for ' + str(silence_counters['In2LSilence']) + ' seconds')
        # if(silence_counters['In3LSilence'] > 30 or silence_counters['In3RSilence'] > 30):
            # print(source_info[2][1] + ' has been silent for ' + str(silence_counters['In3LSilence']) + ' seconds')
        # if(silence_counters['In4LSilence'] > 30 or silence_counters['In4RSilence'] > 30):
            # print(source_info[3][1] + ' has been silent for ' + str(silence_counters['In4LSilence']) + ' seconds')
        # if(silence_counters['In5LSilence'] > 30 or silence_counters['In5RSilence'] > 30):
            # print(source_info[4][1] + ' has been silent for ' + str(silence_counters['In5LSilence']) + ' seconds')
            
    except socket.error:
        logging.info("Connection lost. Attempting to reconnect...")
        reconnect()
