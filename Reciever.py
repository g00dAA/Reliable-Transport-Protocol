from socket import *
import random
from datetime import datetime
import time
import matplotlib.pyplot as plt
from tkinter import messagebox
import colorama
from colorama import Fore
import os

# Set the maximum segment size and the port number
MSS = 1024
port = 12000

# Create a receiver socket and bind it to the port
reciever = socket(AF_INET, SOCK_DGRAM)
reciever.bind(('', port))

# Receive the first packet to determine the image name
packet, addr = reciever.recvfrom(MSS + 8)
name = "image " + str(int.from_bytes(packet[2:4], "little"))

# Try to open the file for writing
try:
    file = open(name + '.png', "wb")
    
except IOError:
    print('Error: Could not open file for writing')

expected_packet = 0
finished = 0
first_packet = 1
recieved_packets = []
recieving_time= []
ack_sent = []
ack_time = []
packets_rec = 0
num_bytes = 0

start = time.perf_counter()

while packet:
    # Generate a random number between 1 and 100
    rand = random.randint(1, 100)
    
    # Simulate a 5% chance of packet loss
    if rand <= 5:
        print(Fore.GREEN,'dropped packet here!')
        packet, addr = reciever.recvfrom(MSS + 8)
        continue
    
    # Record the current time
    now = time.perf_counter()
    
    # Print the arrival time of the first packet
    if first_packet == 1:
        print(Fore.RED, f"First packet of {name} arrived successfully At {now - start:0.5f}")
        first_packet = 0
    
    # Print the arrival time of each packet
    print(Fore.BLACK, f"A Packet is recieved At {now - start:0.5f}")
    
    # Increment the number of packets received
    packets_rec = packets_rec + 1
    
    # Increment the number of bytes received
    num_bytes = num_bytes + len(packet)
    
    # Extract the packet ID and file ID from the packet
    packet_id = packet[0:2]
    file_id = packet[2:4]
    
    # Extract the trailer and data from the packet
    trailer = packet[-4:]
    data = packet[4:-4]
    
    # Record the received packets and their arrival times
    recieved_packets.append(int.from_bytes(packet_id, "little"))
    recieving_time.append((now-start))

    # If finished receiving a file, open a new file for writing
    if finished == 1:
        file = open("image " + str(int.from_bytes(packet[2:4], "little")) + '1.png', "wb")
        finished = 0
        expected_packet = 0
        
        # Reset the list of received packets and their arrival times
        recieving_time= []
        recieved_packets = []
        
    # Check if the packet ID is equal to the expected packet ID
    if int.from_bytes(packet_id, "little") == expected_packet:
        # Print the expected packet ID
        print("It is An expected packet with ID = ", int.from_bytes(packet_id, "little"))
        # Update the last packet ID and file ID
        last_packet_id = packet_id
        last_file_id = file_id
        # Write the data to the file
        file.write(data)
        # Get the packet ID and create an ACK
        ID = int.from_bytes(packet_id, "little")
        ACK = packet_id + file_id
        now = time.perf_counter()
        # Print the time when sending the ACK
        print(f"Sending Acknowledgment for packet {ID} At {now - start:0.5f}")
        reciever.sendto(ACK, addr)
        ack_sent.append(int.from_bytes(last_packet_id, "little"))
        ack_time.append((now-start))
        # Increment the expected packet ID
        expected_packet += 1

        # Check if the trailer is not equal to 0
        if int.from_bytes(trailer, "little") != 0:
            print('tarawa')
            now = time.perf_counter()
            end = now
            num_packets = ID + 1
            # Print that the file reception is completed
            print(Fore.RED, f"File {name} reception is completed At {now - start:0.5f} with packet id {ID}")
            finished = 1
            file.close()
            file_size = os.path.getsize(name+".png")
            break

    elif expected_packet != 0:
        # Print that this is an unexpected packet
        print('This is An unexpected packet with ID =', int.from_bytes(packet_id, "little"))
        # Create an ACK with the last correct packet ID and file ID
        ACK = last_packet_id + last_file_id
        now = time.perf_counter()
        # Print the time when sending the last correct ACK
        print(f"Sending last correct Acknowledgment At {now - start:0.5f}")
        reciever.sendto(ACK, addr)
        ack_sent.append(int.from_bytes(last_packet_id, "little"))
        ack_time.append((now-start))

    # Receive a new packet from the sender
    packet, addr = reciever.recvfrom(MSS + 8)
    
    
    

#Ploting statistics from the receiver percepctive

#ploting receiving time
plt.scatter(recieving_time, recieved_packets, label="packets recieved", color="red", marker="*", s=2)
plt.title('packets recieved at reciever')
plt.ylabel('packet id')
plt.xlabel('time')
plt.legend(loc ="lower right")
plt.show()

#Acknowledgment of the sent packets
plt.scatter(ack_time, ack_sent, label="Acknowledgments sent", color="green", s=2)
plt.title('Acknowledgments sent by reciever')
plt.ylabel('packet id')
plt.xlabel('time')
plt.legend(loc ="lower right")
plt.show()

#file_size is num_file_bytes

net_consumed = end - start
bytes_per_sec = num_bytes / net_consumed
packets_per_sec = packets_rec / net_consumed

last_packet_size = (file_size - ((num_packets - 1) * MSS)) + 8
num_packet_bytes = MSS + 8

messagebox.showinfo("File transfer Info", 
                    f"For {name} \nStart time = {str(start)} \nEnd time = {str(end)} \nElapsed time = {str(net_consumed)} seconds\nNumber of packets resieved = {str(packets_rec)} packet\nFile size = {str(file_size)} byte\nNumber of bytes recieved/packet = {str(num_packet_bytes)} byte\nLast packet size = {str(last_packet_size)} byte\nAverage transfer rate(bytes/sec) = {str(bytes_per_sec)} byte/sec\nAverage transfer rate(packets/sec) = {str(packets_per_sec)} packet/sec")

reciever.close()