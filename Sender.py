from socket import *
from datetime import datetime
import time
import matplotlib.pyplot as plt
import colorama
from colorama import Fore
from tkinter import *
from tkinter import messagebox
import os

# Set the maximum segment size to 1024 bytes
MSS = 1024

# Set the window size to 16 segments
WINDOW_SIZE = 16

# Set the timeout interval to 0.9 seconds
time_out = 0.9

# Define a function to check the current line in a file
def check_line(f):
    pos = f.tell()
    line = f.readline()
    f.seek(pos)
    return line

# Define the server's IP address and port number
serverName = "192.168.1.6"
serverPort = 12000

# Create a UDP socket for the client
clientSocket = socket(AF_INET, SOCK_DGRAM)

# Set the timeout for the socket
clientSocket.settimeout(time_out)

# Define a function to prepare packets from a file
def prep_packet(filename):
    all_packets = []
    try:
        # Open the file in binary read mode
        file = open(filename, 'rb')
        # Read the first segment of data from the file
        file_data = file.read(MSS)
    except IOError:
        print('File isn\'t accessible')

    # Initialize packet ID, trailer ID, and file ID
    packet_id = chr(0).encode('utf-16LE')
    trailer_id_bits = chr(0).encode('utf-32LE')
    file_id = chr(0).encode('utf-16LE')  # **REQUIRES CHANGE** change according to file

    # Loop through the file data and create packets
    while True:
        # Check if we have reached the end of the file
        if not check_line(file):
            trailer_id_bits = bytes.fromhex('ffffffff')

        # Build the packet by concatenating packet ID, file ID, file data, and trailer ID
        packet = packet_id
        packet = packet + file_id
        packet = packet + file_data
        packet = packet + trailer_id_bits

        # Add the packet to the list of packets
        all_packets.append(packet)

        # Increment the packet ID by 1
        packet_id = (chr(ord(packet_id.decode('utf-16LE')) + 1)).encode('utf-16LE')

        # Read the next segment of data from the file
        file_data = file.read(MSS)

        # Check if we have reached the end of the file
        if not file_data:
            print(Fore.BLACK,'Done data reading')
            break

    # Return the list of packets
    return all_packets

im_name = 'LargFile.jpg'
file_size = os.path.getsize(im_name)

all_packets = prep_packet(im_name)
i = 0
transmitted_packets = []
retransmitted_packets = []
sending_time = []
resending_time = []
first_packet = 1
packets_sent = 0
bytes_sent = 0
num_lastPacket_sent = 0
last_sent_packetID = 0
startWindow = 0
endWindow = 0
retransmitions = 0
retransmit = 0

#used to calculate how many times the last packet was sent 
last_packet_id =  int.from_bytes(all_packets[len(all_packets) - 1][0:2], "little") 

start = time.perf_counter()
while i < len(all_packets):
    
    for j in range(0, WINDOW_SIZE):
        
        if startWindow + j < len(all_packets):
            packetTosend = all_packets[startWindow + j]
            
            # Extract packet ID from first two bytes of packet
            ID = int.from_bytes(packetTosend[0:2], "little")
            
            # Send packet to server
            clientSocket.sendto(all_packets[startWindow + j], (serverName, serverPort))
            
            # Keep track of number of sent bytes
            bytes_sent += len(all_packets[startWindow + j])  
            
            # Keep track of number of last packets sent
            if ID == last_packet_id:
                num_lastPacket_sent = num_lastPacket_sent + 1
                
            # Keep track of number of packets sent
            packets_sent = packets_sent + 1
            
            # Keep track of last sent packet ID
            last_sent_packetID = ID
            
            # Get current time
            now = time.perf_counter()  
            
            # Print message if first packet is sent successfully
            if first_packet == 1:
                print(Fore.RED, f"First packet of {im_name} is successfully sent at time: {now - start:0.5f}")
                first_packet = 0
            
            # Print message for each packet sent
            print(Fore.BLACK, f"packet {ID} is sent at time: {now - start:0.5f}")
            
            # Update end window index
            endWindow = startWindow + j
            
            # Keep track of transmitted packets and sending time
            if retransmit == 0:
                sending_time.append(now-start)
                transmitted_packets.append(ID)
                
            # Keep track of retransmitted packets and resending time
            else:
                resending_time.append(now-start)
                retransmitted_packets.append(ID)
                retransmitions = retransmitions + 1
                
    expectedAck = 0
    while 1:
        retransmit = 1
        try:
            while 1:
                # Receive acknowledgement from server
                rec_Ack, serverAddress = clientSocket.recvfrom(MSS + 8)
                
                # Extract packet ID and file ID from acknowledgement packet
                packet_id = rec_Ack[0:2] 
                file_id = rec_Ack[2:4]
                
                # Convert packet ID to integer
                rec_Ack_id = int.from_bytes(packet_id, "little")
                
                # Get current time
                now = time.perf_counter()   
                
                # Print message for each acknowledgement received
                print(Fore.BLACK,f"acknowledge for packet {rec_Ack_id} is recieved At {now - start:0.5f}")

                # Update expected acknowledgement number if received acknowledgement number is less than
                # or equal to expected acknowledgement number
                if expectedAck <= rec_Ack_id:
                    expectedAck = rec_Ack_id + 1
                    
                    # Update window indices
                    i = rec_Ack_id + 1
                    startWindow = rec_Ack_id + 1
                    endWindow = rec_Ack_id + WINDOW_SIZE
                    
                    # Check if end window index exceeds number of packets
                    if endWindow > len(all_packets) - 1:
                        endWindow = len(all_packets) - 1
                        
                    # Send packets in window using sliding window protocol
                    if (endWindow - startWindow + 1) == WINDOW_SIZE:
                        pID = int.from_bytes(all_packets[startWindow][0:2], "little")
                        
                        for j in range(0, WINDOW_SIZE):
                            if pID > last_sent_packetID:
                                clientSocket.sendto(all_packets[startWindow + j], (serverName, serverPort))
                                bytes_sent = bytes_sent + len(all_packets[startWindow + j])  
                                
                                if pID == last_packet_id:
                                    #incerement the last packet counter by 1
                                    num_lastPacket_sent += 1
                                    
                                #increment the number of sent packets
                                packets_sent = packets_sent + 1
                                now = time.perf_counter() 

                                if int.from_bytes(all_packets[startWindow + j][-4:], "little") != 0:
                                    # store the end time of the process
                                    end = time.perf_counter() 
                                    
                                    # Print message for last packet sent
                                    print(Fore.GREEN, f"Last packet of {im_name} with id {pID} is successfully sent at time: {now - start:0.5f}")
                                    
                                else:
                                    # Print message for each packet sent
                                    print(Fore.BLACK, f"packet {pID} is sent at time: {now - start:0.5f}")
                                    
                                # Update last sent packet ID
                                last_sent_packetID = pID

                                # Extract packet ID from packet
                                ID = int.from_bytes(all_packets[startWindow + j][0:2], "little")

                                # Append transmitted packets and sending time to lists
                                sending_time.append(now-start)
                                transmitted_packets.append(ID)
                                
                            # Increment packet ID
                            pID += 1
                    break


        except OSError:
            now = time.perf_counter()   
            print(f"timed out i At {now - start:0.5f}")
            break


#Ploting statistics from the receiver percepctive
#num_file_bytes is the file size

elspsed_time = end - start
num_packet_bytes = MSS + 8
#Ensure the received number from counting
num_packets = len(all_packets) + retransmitions  
loss_rate = (retransmitions / packets_sent) * 100
bytes_per_sec = bytes_sent / elspsed_time
packets_per_sec = packets_sent / elspsed_time

last_packet_size = (file_size - ((len(all_packets) - 1) * MSS)) + 8

#plot both transmitted and retransmitted packets
plt.scatter(sending_time, transmitted_packets, label="Transmitted packets", color="red", marker="*", s=2)
plt.scatter(resending_time, retransmitted_packets, label="Retransmitted packets", color="green", marker="*", s=2)
plt.title('packets sent at sender')
plt.ylabel('packet id')
plt.xlabel('time')
plt.legend(loc ="lower right")

plt.figtext(1, 
            0.5, 
            f"For {im_name} \nNumber of Retransmissions = {str(retransmitions)} \nTimeout interval = {str(time_out)} seconds\nThe window size = {str(WINDOW_SIZE)} packets\nMaximun sigment size = {str(MSS)} bytes\nLoss rate = {str(loss_rate)} \%",
            fontsize = 10)
plt.show()

messagebox.showinfo("File transfer Info", 
                    f"For {im_name} \nStart time = {str(start)} \nEnd time = {str(end)} \nElapsed time, = {str(elspsed_time)}seconds\nNumber of packets sent = {str(packets_sent)} packet\nFile size = {str(file_size)} byte\nNumber of bytes/packet = {str(num_packet_bytes)} byte\nLast packet size = {str(last_packet_size)} byte\nNumber of retransmissions = {str(retransmitions)} \nAverage transfer rate(bytes/sec) = {str(bytes_per_sec)} byte/sec\nAverage transfer rate(packets/sec) = {str(packets_per_sec)} packet/sec")

clientSocket.close()
