import asyncio
import sys
import struct
from bleak import BleakClient
from bleak import BleakScanner
import sqlite3

import datetime

import os.path
from pathlib import PurePath

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
MY_PATH = PurePath(SCRIPT_PATH)

DBNAME = MY_PATH/'t_h_readings.db'

dev_name = 'ATC_699848' # change with the name of your device
dev_addr = 'A4:C1:38:69:98:48' # change with the address of your device

index = '0000181a-0000-1000-8000-00805f9b34fb' # do not change

def insert_record(temp, humi, batt_volt, batt_perc):
    ts = datetime.datetime.now()
    print(f'Inserisco {ts}, {temp}, {humi}, {batt_volt}, {batt_perc}')
    con  = sqlite3.connect(DBNAME)
    with con:
        cur = con.cursor()
        con.row_factory = sqlite3.Row

        cur.execute('''INSERT INTO reading (timestamp, temperature, humidity, battery_voltage, battery_percent)
                VALUES (?, ?, ?, ?, ?);''',
                (ts, temp, humi, batt_volt, batt_perc))
        con.commit()
    
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
                data = advertising_data.service_data[index]
                data = raw_packet_to_str(data)
                temperature = int.from_bytes(bytearray.fromhex(data[12:16]),byteorder='big',signed=True) / 10.
                humidity = int(data[16:18], 16)
                batteryVoltage = int(data[20:24], 16) / 1000
                batteryPercent = int(data[18:20], 16)
                insert_record(temperature, humidity, batteryVoltage, batteryPercent)
                stop_event.set()

    except KeyboardInterrupt:
            stop_event.set()


    async with BleakScanner(callback) as scanner:
        await stop_event.wait()


asyncio.run(main())
