import socket
import selectors
import os

commands = []
requests = []
request_methods = []
filenames = []
file_types = []
host_names = []
port_numbers = []
cached_objects = {}
sel = selectors.DefaultSelector()

with open('commands.txt', encoding='UTF-8', mode='r') as f:
    commands = f.readlines()

def parse_file():
    for count in range(len(commands)):
        request_method = commands[count].split(' ')[0]
        request_methods.append(request_method)

        filename = commands[count].split(' ')[1]
        filenames.append(filename)

        file_type = filename.split(".")[1]
        file_types.append(file_type)

        host_name = commands[count].split(' ')[2].strip('\n')
        host_names.append(host_name)

        try:
            port_number = commands[count].split(' ')[3].strip('\n')
            port_numbers.append(port_number)
        except Exception as e:
            port_number = 80
            port_numbers.append(port_number)

        requests.append(generate_request(request_method, filename, host_name))

def generate_request(request_method, filename, host_name):
    request = ''
    if request_method == "GET":
        request += request_method + ' /' + filename + ' HTTP/1.0\r\n'
        request += 'Host:' + host_name + '\r\n\r\n'

    elif request_method == "POST":
        request += request_method + ' /' + filename + ' HTTP/1.0\r\n'
        request += 'Host:' + host_name + '\r\n'
        request += '\r\n'
        f = open(filename,"r")
        request += f.read()

    return request

def start_connections(host, port, request, filename, request_method, file_type):
    server_addr = (host, port)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    print(f"Starting connection to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect_ex(server_addr)
    sock.sendall(bytes(request, 'UTF-8'))
    if file_type == 'jpg' or file_type == 'jpeg' or file_type == 'png':
        data = sock.recv(4092)
        image = sock.recv(12288)
        response = data.decode() + str(image)
    else:
        data = sock.recv(4092)
        response = data.decode()
    cached_objects[request] = response
    fileReady = "Clientfiles/"
    head, tail = os.path.split(filename)
    fileReady += tail
    try:
        if request_method == "GET":
            if file_type == 'jpg' or file_type == 'jpeg' or file_type == 'png':
                f = open(fileReady, "wb")
                f.write(image)
                f.close()
            else:
                payload = response.split('\r\n\r\n', 1)[1]
                f = open(fileReady, "w")
                f.write(payload)
                f.close()
    except Exception as e:
        print(e)

    print("From Server: ", response)
    print("\n")
    sel.register(sock, events)


def check_cache(request):
    for i in range(len(commands)):
        request = requests[i]
        if request in cached_objects.keys():
            response = cached_objects[request]
            print("\nRESPONSE From CACHE: " + response + "\n\n")
        else:
            start_connections(host_names[i], int(port_numbers[i]), requests[i], filenames[i], request_methods[i], file_types[i])

parse_file()

check_cache(generate_request)