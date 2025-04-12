import serial.tools.list_ports
import serial.serialutil

ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()

# portList = []

# for onePort in ports:
#     portList.append(str(onePort))
#     print(str(onePort))

# val = input("select Port: COM")

# for x in range(0, len(portList)):
#     if portList[x].startswith("COM" + str(val)):
#         portVar = "COM" + str(val)
#         print(portList(x))

serialInst.baudrate = 115200
serialInst.port = '/dev/cu.usbserial-110'
serialInst.open()

while True:
    try:
        if serialInst.in_waiting:
            packet = serialInst.readline()
            print(packet.decode('utf-8'))
    except serial.serialutil.SerialException:
        pass