import socket
import time
import threading
import signal
import sys
import os

PACKET_SIZE = 1024
PORT = 8085
http_11_requests = []

def shutdown_server(signal, frame):
    print("Server shutdown command recieved (ctrl+C), shutting down/closing server...")
    s.close()
    sys.exit(1)

# Generates http response headers based on http protocol version and response code
def generate_header(response_code, http_version, file_type):
    header = ''
    time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())

    # If http version is 1.0, close connection after serving response
    if http_version == '1.0':
        if response_code == 200:
            header += 'HTTP/1.0 200 OK\n'
        if response_code == 404:
            header += 'HTTP/1.0 404 Not Found\n'
        header += 'Date: ' + time_now + '\n'
        header += 'Server: Our server\n'
        header += 'Connection: close\n'  

    # If http version is 1.1, keep connection alive after serving response
    elif http_version == '1.1':
        if response_code == 200:
            header += 'HTTP/1.1 200 OK\n'
        elif response_code == 404:
            header += 'HTTP/1.1 404 Not Found\n'
        header += 'Date: ' + time_now + '\n'
        header += 'Server: Our server\n'
        header += 'Connection: keep-alive\n' 

    if file_type == 'html':
        header += 'Content-Type: text/html\n\n'
    elif file_type == 'jpg' or file_type == 'jpeg':
        header += 'Content-Type: image/jpeg\n\n'
    elif file_type == 'png':
        header += 'Content-Type: image/png\n\n'
    else:
        header += 'Content-Type: ' + file_type + '\n\n'
    return header


# Read, decode, and respond to client through socket connection
def deal_with_client(client_socket, address):
    persistent_connection = False
    while True:
        try:
            # Recive request (packet) from client and decode
            message = client_socket.recv(PACKET_SIZE).decode()
            response_data = "\r\n\r\n"

            # If no message recieved from client close connection and break
            if not message:
                print("No message recieved, closing client connection...")
                client_socket.close()
                break

            # Get request type and version from client request
            try:
                request_method = message.split(' ')[0]
                sample_str = message.split('\n')[0]
                # Get last 3 character
                http_version = sample_str[-4:-1]
                print("Method: " + request_method + '\n')
                print("Request Body: \n" + message)
                print("HTTP Version: " + http_version + '\n')
            except Exception as e:
                print("Error getting request method/http version/message")
                print("Closing client socket...")
                client_socket.close()
                break

            # Set the socket to timeout after 10 seconds if http version is 1.1 (persistent connection)
            if http_version == '1.1' and persistent_connection == False:
                persistent_connection = True
                client_socket.settimeout(10)

                # All the requests are saved in a list then after timeout
                # the server will read each one of them from the list 
                # and respond to them the same order they were received

                #start_time = time.time()
                #seconds = 10
                #while True:
                    #http_11_requests.append(message)
                    #current_time = time.time()
                    #elapsed_time = current_time - start_time
                    #if elapsed_time > seconds:
                        #message = client_socket.recv(PACKET_SIZE).decode()
                        #http_11_requests.append(message)
                        #print("\n[Pipelined] stop receiving requests after 10 seconds and start responding\n")
                        #break

            if request_method == "GET" or request_method == "HEAD":
                try:
                    file_requested = message.split(' ')[1]
                    if file_requested == "/":
                        file_requested = "template/index.html"

                    file_type = file_requested.split('.')[1]
                    print("File requested by client: " + file_requested)
                    print("Filetype of file: " + file_type)
                except Exception as e:
                    print("Error getting filetype/requested file")
                    print("Closing client socket...")
                    client_socket.close()
                    break

                filepath_to_serve = "template" + file_requested
                print("Filepath to serve: " + filepath_to_serve + '\n')

                if file_type == 'html':
                    try:
                        if request_method == "GET":
                            file = open(filepath_to_serve, 'r')

                            response_data += file.read()
                            file.close()
                        response_header = generate_header(200, http_version, file_type)
                        response_code = 200
                    except Exception as e: 
                        print("File not found, serving 404 file not found response")
                        response_header = generate_header(404, http_version,
                                                          file_type)
                        response_code = 404

                    if request_method == "GET" and response_code == 200:
                        print("Sending: \n" + response_header + response_data)
                        client_socket.send(response_header.encode() + response_data.encode())
                    else:
                        print("Sending: \n" + response_header)
                        client_socket.send(response_header.encode())

                elif file_type == 'txt':
                    try:
                        if request_method == "GET": 
                            file = open(filepath_to_serve, 'r')
                            response_data += file.read()
                            file.close()
                        response_header = generate_header(200, http_version, file_type)
                        response_code = 200
                    except Exception as e:
                        print("File not found, serving 404 file not found response")
                        response_header = generate_header(404, http_version,
                                                          file_type)
                        response_code = 404

                    if request_method == "GET" and response_code == 200:
                        print("Sending: \n" + response_header + response_data)
                        client_socket.send(response_header.encode() + response_data.encode())
                    else:
                        print("Sending: \n" + response_header)
                        client_socket.send(response_header.encode())

                elif file_type == "jpg" or file_type == "jpeg" or file_type == "png":
                    try:
                        if request_method == "GET":
                            file = open(filepath_to_serve, 'rb')
                            response_data = file.read()
                            file.close()
                        response_header = generate_header(200, http_version, file_type)
                        response_code = 200
                    except Exception as e:
                        print("Image not found/couldn't be opened, serving 404 file not found response")
                        response_header = generate_header(404, http_version,
                                                          file_type)
                        response_code = 404
                    if request_method == "GET" and response_code == 200:
                        print("Sending image with: \n" + response_header)
                        client_socket.send(response_header.encode())
                        client_socket.send(response_data)
                    else:
                        print("Sending: \n" + response_header)
                        client_socket.send(response_header.encode())

                else:
                    print("Invalid requested filetype: " + file_type)
                    response_header = generate_header(404, http_version, file_type)
                    print("Sending: \n" + response_header)
                    client_socket.send(response_header.encode())

                # If http version 1.0, want to close connection after completing request
                if http_version == '1.0':
                    print("\nClosing client socket...\n")
                    client_socket.close()
                    break

                # Else if http version 1.1, want to keep persistent connection after completing request
                elif http_version == '1.1' and persistent_connection == True:
                    print("http 1.1: peristent connection, continuing to recieve requests...")

            # If The request is POST
            elif request_method == "POST":
                fileName0 = message.split(' ')[1]
                myfilename = fileName0.split(' ')[0]
                messagebody = message.split('\r\n\r\n')[1]
                file_type = myfilename.split('.')[1]
                head, tail = os.path.split(myfilename)

                python_file = open(tail, "w")
                python_file.write(messagebody)
                python_file.close()
                response_header = generate_header(200, http_version, file_type)
                client_socket.send(response_header.encode())
                print("\nClosing client socket...\n")
                client_socket.close()
                break

            else:
                print("Error: Unknown HTTP request method: " + request_method)
                print("\nClosing client socket...\n")
                client_socket.close()
                break

        # Exception is thrown once the socket connection times out (http 1.1 - persistent connection)
        except socket.timeout:
            print("Socket connection timeout reached (10 seconds), closing client socket...")
            client_socket.close()
            break


# Set up ctrl+C command inturrupt
signal.signal(signal.SIGINT, shutdown_server)

# Create a socket object
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Make socket address reusable
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print("Socket successfully created")

# Next bind localhost IP to the port
try:
    s.bind(('localhost', PORT))
    print("socket binded to", PORT)
except Exception as e:  # Exit if socket could not be bound to port
    print("Error: could not bind to port: " + PORT)
    s.close()
    sys.exit(1)

# Have the socket listen for up to 5 connections
s.listen(5)
print("socket is listening for connections, Ctrl+C and refresh localhost in browser to close server\n")

while True:
    # Accept new connection from incoming client
    client_socket, address = s.accept()
    print('Got connection from', address, '\n\n\n')
    # Create new thread to deal with client request, and continue accepting connections
    threading.Thread(target=deal_with_client, args=(client_socket, address)).start()