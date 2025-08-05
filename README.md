# Reliable-Transport-Protocol

Introduction & Objectives:
- The implementation of transport protocols that ensure reliable data transfer is crucial in modern computer networks. In this project, we will focus on augmenting the User Datagram Protocol (UDP) with the Go-Back-N (GBN) protocol to provide reliability services.
- The main objective of this project is to implement a special GBN sender and receiver that will provide reliable data transfer services over the unreliable UDP. Specifically, we aim to design and develop a protocol that will ensure that all data sent by the sender is received by the receiver without any loss, duplication or out of order delivery.

 
Brief: As a brief, the protocol undergoes the following steps:
- To transmit a file to a receiver, the sender first divides the file into parts, each consisting of a specific number of bytes called the maximum segment size (MSS).
- The sender then sends packets to the receiver, which contain information such as packet and file IDs, application data, and a trailer.
- The sender sends a number of segments equal to the window size (N) and waits for acknowledgement from the receiver within a certain timeout.
- If the sender receives the acknowledgement before the timeout expires, it moves the window forward and sends new packets.
- If the sender does not receive the expected acknowledgement, it resends the packets in the window, starting from the last one for which acknowledgement was not received.
