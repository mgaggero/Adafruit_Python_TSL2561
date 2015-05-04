# Copyright (c) 2015 Massimo Gaggero
# Author: Massimo Gaggero
import time
import logging

# # TSL2561 default address.
TSL2561_FLOAT_I2CADDR            = 0x39
TSL2561_GND_I2CADDR              = 0x29
TSL2561_VDD_I2CADDR              = 0x49

# TSL2561 Registers
TSL2561_REGISTER_CONTROL          = 0x00
TSL2561_REGISTER_TIMING           = 0x01
TSL2561_REGISTER_THRESHHOLDL_LOW  = 0x02
TSL2561_REGISTER_THRESHHOLDL_HIGH = 0x03
TSL2561_REGISTER_THRESHHOLDH_LOW  = 0x04
TSL2561_REGISTER_THRESHHOLDH_HIGH = 0x05
TSL2561_REGISTER_INTERRUPT        = 0x06
TSL2561_REGISTER_CRC              = 0x08
TSL2561_REGISTER_ID               = 0x0A
TSL2561_REGISTER_CHAN0_LOW        = 0x0C
TSL2561_REGISTER_CHAN0_HIGH       = 0x0D
TSL2561_REGISTER_CHAN1_LOW        = 0x0E
TSL2561_REGISTER_CHAN1_HIGH       = 0x0F

# TSL2561 Command Register Bits
TSL2561_COMMAND_BIT               = 0x80
TSL2561_CLEAR_BIT                 = 0x40
TSL2561_WORD_BIT                  = 0x20
TSL2561_BLOCK_BIT                 = 0x10

# TSL2561 Control Register Fields
TSL2561_CONTROL_POWERON           = 0x03
TSL2561_CONTROL_POWEROFF          = 0x00

# TSL2561 Integration Periods
TSL2561_INTEGRATIONTIME_13MS      = 0x00
TSL2561_INTEGRATIONTIME_101MS     = 0x01
TSL2561_INTEGRATIONTIME_402MS     = 0x02

TSL2561_DELAY_INTTIME_13MS        = 15
TSL2561_DELAY_INTTIME_101MS       = 120
TSL2561_DELAY_INTTIME_402MS       = 450


class TSL2561(object):
    def __init__(self, address=TSL2561_FLOAT_I2CADDR, i2c=None, **kwargs):
        self._logger = logging.getLogger('Adafruit_TSL2561.TSL2561')
        # Check that mode is valid.
        # if mode not in [HTU21D_HOLDMASTER, HTU21D_NOHOLDMASTER]:
        #     raise ValueError('Unexpected mode value {0}.  Set mode to one of HTU21D_HOLDMASTER, HTU21D_NOHOLDMASTER'.format(mode))
        # self._mode = mode
        # Create I2C device.
        if i2c is None:
            import Adafruit_GPIO.I2C as I2C
            i2c = I2C
        self._device = i2c.get_i2c_device(address, **kwargs)
        self._tsl2561IntegrationTime = TSL2561_DELAY_INTTIME_402MS

    def _enable(self):
        self._device.write8(TSL2561_COMMAND_BIT | TSL2561_REGISTER_CONTROL, TSL2561_CONTROL_POWERON)

    def _disable(self):
        self._device.write8(TSL2561_COMMAND_BIT | TSL2561_REGISTER_CONTROL, TSL2561_CONTROL_POWEROFF)

    def read_raw_luminosity(self):
        """Reads the raw luminosity from the sensor."""
        self._enable()

        if self._tsl2561IntegrationTime == TSL2561_INTEGRATIONTIME_13MS:
            time.sleep(TSL2561_DELAY_INTTIME_13MS/1000.0)
        elif self._tsl2561IntegrationTime == TSL2561_INTEGRATIONTIME_101MS:
            time.sleep(TSL2561_DELAY_INTTIME_101MS/1000.0)
        else:
            time.sleep(TSL2561_DELAY_INTTIME_402MS/1000.0)

        # Reads a two byte value from channel 0 (visible + infrared)
        broadband = self._device.readU16LE(TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CHAN0_LOW)

        # Reads a two byte value from channel 1 (infrared)
        ir = self._device.readU16LE(TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CHAN1_LOW)

        self._disable()

        return broadband, ir

    def read_id(self):
        """Reads the Device ID and Revision Number of the sensor."""
        val = self._device.readU8(TSL2561_REGISTER_ID)

        self._disable()

        # return (val & 0xF0) << 8, (val & 0x0F)
        return val

    def read_lux(self):

        ch0, ch1 = self.read_raw_luminosity()
        ratio = 0.0

        if ch0 != 0:
            ratio = float(ch1) / float(ch0)

        lux = 0.0

        if 0 < ratio <= 0.5:
            lux = 0.0304 * ch0 - 0.062 * ch0 * (ch1/ch0) ** 1.4
        elif 0.5 < ratio <= 0.61:
            lux = 0.0224 * ch0 - 0.031 * ch1
        elif 0.61 < ratio <= 0.80:
            lux = 0.0128 * ch0 - 0.0153 * ch1
        elif 0.80 < ratio <= 1.30:
            lux = 0.00146 * ch0 - 0.00112 * ch1
        elif ratio > 1.30:
            lux = 0.0

        return lux
