import asyncio
from dataclasses import dataclass
import sys
import struct
from bleak import BleakClient
from bleak import BleakScanner

from datetime import datetime
from matplotlib import pyplot
from matplotlib.animation import FuncAnimation

dev_name = 'ATC_699848'
dev_addr = 'A4:C1:38:69:98:48'
index = '0000181a-0000-1000-8000-00805f9b34fb'

x_data, y_data = [], []
figure = pyplot.figure()
line, = pyplot.plot_date(x_data, y_data, '-')

def update(frame):
    '''
    x_data.append(datetime.now())
    y_data.append(randrange(0, 100))
    '''
    line.set_data(x_data, y_data)
    figure.gca().relim()
    figure.gca().autoscale_view()
    return line,

animation = FuncAnimation(figure, update, interval=2000)

#pyplot.ion()
pyplot.show(block=False)

def raw_packet_to_str(pkt):
    """
    Returns the string representation of a raw HCI packet.
    """
    if sys.version_info > (3, 0):
        return ''.join('%02x' % struct.unpack("B", bytes([x]))[0] for x in pkt)
    else:
        return ''.join('%02x' % struct.unpack("B", x)[0] for x in pkt)

async def main():
    stop_event = asyncio.Event()

    try:
        def callback(device, advertising_data):
            if device.name == dev_name:
                #'''
                data = advertising_data.service_data[index]
                data = raw_packet_to_str(data)
                temperature = int.from_bytes(bytearray.fromhex(data[12:16]),byteorder='big',signed=True) / 10.
                print(f"Temp: {temperature}")
                humidity = int(data[16:18], 16)
                print(f"Humi: {humidity}")
                batteryVoltage = int(data[20:24], 16) / 1000
                #print(batteryVoltage)
                batteryPercent = int(data[18:20], 16)
                #print(batteryPercent)
                x_data.append(datetime.now())
                y_data.append(temperature)
                line.set_data(x_data, y_data)
                figure.gca().relim()
                figure.gca().autoscale_view()
                '''
                data = advertising_data.service_data[index]
                data_str = raw_packet_to_str(data)
                measurement = Measurement(0,0,0,0,0,0,0,0)
                measurement = decode_data_atc(dev_addr, 'adv_type', data_str, 'rssi', measurement)
                print(measurement)
                '''

    except KeyboardInterrupt:
            stop_event.set()


    async with BleakScanner(callback) as scanner:
        ...
        # Important! Wait for an event to trigger stop, otherwise scanner
        # will stop immediately.
        await stop_event.wait()

    # scanner stops when block exits
    ...

asyncio.run(main())
