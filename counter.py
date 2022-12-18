import spidev
import RPi.GPIO as GPIO
import i2clcda as lcd
import time
import datetime

V_REF = 3.29476
CHN = 0
LED = 25
BUTTON = 23
WAIT = 0.2

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT)
GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000


def get_voltage():
    dout = spi.xfer2([((0b1000+CHN) >> 2)+0b100,
                     ((0b1000+CHN) & 0b0011) << 6, 0])
    bit12 = ((dout[1] & 0b1111) << 8) + dout[2]
    volts = round((bit12 * V_REF) / float(4095), 4)
    return volts


try:
    recents = []
    avg = 0
    new = 0
    count = 0
    status = False
    print('--- start ---')
    lcd.lcd_init()
    while True:
        volts = get_voltage()
        if len(recents) < 3:
            recents.append(volts)
        else:
            recents.pop(0)
            recents.append(volts)
            new = sum(recents)/3
        if not status and avg * 0.9 > new:
            GPIO.output(LED, GPIO.HIGH)
            status = True
            count += 1
            if count == 1:
                time_start = time_last = time.time()
            time_last = time.time()
            lcd.lcd_string(str(count), lcd.LCD_LINE_1)
            elapsed = str(datetime.timedelta(
                seconds=(time_last - time_start))).split(".")[0]
            lcd.lcd_string(elapsed, lcd.LCD_LINE_2)
            print(str(count) + " " + elapsed, flush=True)
        elif status and new > avg:
            GPIO.output(LED, GPIO.LOW)
            status = False
#        print('OFF volts= {:3.2f}'.format(avg))
        avg = new
        if (GPIO.input(BUTTON) == 0):
            print('reset')
            count = 0
            lcd.lcd_string(str(count), lcd.LCD_LINE_1)
            lcd.lcd_string('', lcd.LCD_LINE_2)
        if (count > 0 and datetime.timedelta(seconds=(time.time() - time_last)).total_seconds() > 120):
            lcd.lcd_string(str(count) + " END", lcd.LCD_LINE_1)
            break
        time.sleep(WAIT)

except KeyboardInterrupt:
    pass
finally:
    spi.close()
    GPIO.cleanup()
    print('--- stop ---')
