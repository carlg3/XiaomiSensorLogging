import asyncio, sys, struct, sqlite3, datetime, os.path, threading, logging, time
from pathlib import PurePath
from bleak import BleakClient
from bleak import BleakScanner

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

index = '0000181a-0000-1000-8000-00805f9b34fb' # do not change

class Termometro():
    def __init__(self, pseudo_name, dev_name, dev_addr, index, DBNAME): # , tmp_lettura):
        self.DBNAME = DBNAME
        self.pseudo_name = pseudo_name 
        self.dev_name = dev_name
        self.dev_addr = dev_addr
        self.index = index
        self.tmp_lettura = Lettura()

class Lettura():
    def __init__(self, temperature = 0, humidity = 0, batteryVoltage = 0, batteryPercent = 0):
        self.temperature = temperature
        self.humidity = humidity
        self.batteryVoltage = batteryVoltage
        self.batteryPercent = batteryPercent

    def isEqual(self, l_new):
        # returns true if the readings are equal, false otherwise
        return (self.temperature == l_new.temperature and self.humidity == l_new.humidity and self.batteryVoltage == l_new.batteryVoltage and self.batteryPercent == l_new.batteryPercent)

class Util:
    def insert_record(t, temp, humi, batt_volt, batt_perc, DEBUG=False, self=None):
        ts = datetime.datetime.now()
        # ts: {ts},
        logger.info(f'[{t.pseudo_name}]: [temp: {temp}, humi: {humi}, batt_volt: {batt_volt}, batt_perc: {batt_perc}]')

        if DEBUG is False:
            con  = sqlite3.connect(t.DBNAME)
            with con:
                cur = con.cursor()
                con.row_factory = sqlite3.Row

                cur.execute('''INSERT INTO reading (timestamp, temperature, humidity, battery_voltage, battery_percent)
                        VALUES (?, ?, ?, ?, ?);''',
                        (ts, temp, humi, batt_volt, batt_perc))
                con.commit()
        
    def raw_packet_to_str(pkt, self=None):
        """
        Returns the string representation of a raw HCI packet.
        """
        if sys.version_info > (3, 0):
            return ''.join('%02x' % struct.unpack("B", bytes([x]))[0] for x in pkt)
        else:
            return ''.join('%02x' % struct.unpack("B", x)[0] for x in pkt)

class Scanner:
    def __init__(self, t1, t2, wait_time):
        self.wait_time = wait_time
        self.t1 = t1
        self.t2 = t2

    def aspetta(self):
        logger.info(f'Stopping pooling for {self.wait_time}..')
        time.sleep(self.wait_time)
        logger.info('Restarting pooling..')

    def smista(self, t, advertising_data):
        data = advertising_data.service_data[index]
        data = Util.raw_packet_to_str(data)

        temperature     = int.from_bytes(bytearray.fromhex(data[12:16]),byteorder='big',signed=True) / 10.
        humidity        = int(data[16:18], 16)
        batteryVoltage  = int(data[20:24], 16) / 1000
        batteryPercent  = int(data[18:20], 16)

        # new obj Lettura
        new = Lettura(temperature, humidity, batteryVoltage, batteryPercent)
        # check for new data
        if t.tmp_lettura.isEqual(new) == False:
            logger.info(f'[{t.pseudo_name}]: Got new data! Saving..')
            Util.insert_record(t, temperature, humidity, batteryVoltage, batteryPercent, DEBUG=False)
            # update old value
            t.tmp_lettura = new
        # else:
        #     logger.info(f'[{t.pseudo_name}]: No new data!')
            
    async def get_data(self):
        stop_event = asyncio.Event()

        try:
            def callback(device, advertising_data):
                if device.name == self.t1.dev_name:
                    self.smista(self.t1, advertising_data)
                    # self.aspetta()
                if device.name == self.t2.dev_name:
                    self.smista(self.t2, advertising_data)
                    # self.aspetta()

        except KeyboardInterrupt:
                stop_event.set()

        async with BleakScanner(callback) as scanner:
            await stop_event.wait()

    def start(self):
        logger.info("Reading in progress..")
        try:
            asyncio.run(self.get_data())
        except KeyboardInterrupt:
            logger.error("Stopping reading..")

WAIT = 0.125*60

TERM_CARLG = Termometro('TermCarlg', 'ATC_5A27F5', 'A4:C1:38:5A:27:F5', index, './temp_1.db') # , Lettura())
TERM_MARTI = Termometro('TermMarti', 'ATC_E7A69F', 'A4:C1:38:E7:A6:9F', index, './temp_2.db') # , Lettura())

ScannerPkts = Scanner(TERM_CARLG, TERM_MARTI, WAIT)
ScannerPkts.start()
