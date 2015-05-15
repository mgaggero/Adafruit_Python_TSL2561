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

# TSL2561 Package Type
TSL2561_PACKAGE_T                 = 0x01
TSL2561_PACKAGE_FN                = 0x02
TSL2561_PACKAGE_CL                = 0x04
TSL2561_PACKAGE_CS                = 0x10

# TSL2561 Gain Bit
TSL2561_GAIN_1x                   = 0x00
TSL2561_GAIN_16x                  = 0x10


class TSL2561(object):
    def __init__(self, address=TSL2561_FLOAT_I2CADDR, package=TSL2561_PACKAGE_T, i2c=None, **kwargs):
        self._logger = logging.getLogger('Adafruit_TSL2561.TSL2561')
        # Check the package is valid.
        if package not in [TSL2561_PACKAGE_T, TSL2561_PACKAGE_FN, TSL2561_PACKAGE_CL, TSL2561_PACKAGE_CS]:
            raise ValueError('Unexpected package value {0}.  Set package to one of TSL2561_PACKAGE_T, TSL2561_PACKAGE_FN, TSL2561_PACKAGE_CL, TSL2561_PACKAGE_CS'.format(package))
        self._package = package
        # Create I2C device.
        if i2c is None:
            import Adafruit_GPIO.I2C as I2C
            i2c = I2C
        self._device = i2c.get_i2c_device(address, **kwargs)

        self._integration_time = TSL2561_INTEGRATIONTIME_402MS
        self._gain = TSL2561_GAIN_1x

        self.set_integration_time(self._integration_time)
        self.set_gain(self._gain)

    def _enable(self):
        self._device.write8(TSL2561_COMMAND_BIT | TSL2561_REGISTER_CONTROL, TSL2561_CONTROL_POWERON)

    def _disable(self):
        self._device.write8(TSL2561_COMMAND_BIT | TSL2561_REGISTER_CONTROL, TSL2561_CONTROL_POWEROFF)

    def read_raw_luminosity(self):
        """Reads the raw luminosity from the sensor."""
        self._enable()

        if self._integration_time == TSL2561_INTEGRATIONTIME_13MS:
            time.sleep(TSL2561_DELAY_INTTIME_13MS/1000.0)
        elif self._integration_time == TSL2561_INTEGRATIONTIME_101MS:
            time.sleep(TSL2561_DELAY_INTTIME_101MS/1000.0)
        else:
            time.sleep(TSL2561_DELAY_INTTIME_402MS/1000.0)

        # Reads a two byte value from channel 0 (visible + infrared)
        broadband = self._device.readU16LE(TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CHAN0_LOW)

        # Reads a two byte value from channel 1 (infrared)
        ir = self._device.readU16LE(TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CHAN1_LOW)

        self._disable()

        return broadband, ir

    def read_id_register(self):
        """Reads the Device ID and Revision Number of the sensor."""
        self._enable()
        val = self._device.readU8(TSL2561_COMMAND_BIT | TSL2561_REGISTER_ID)
        self._disable()

        return val

    def read_timing_register(self):
        """Reads the Timing Register of the sensor."""
        self._enable()
        val = self._device.readU8(TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING)
        self._disable()

        return val & 0xFF

    def set_integration_time(self, itime):
        if itime not in [TSL2561_INTEGRATIONTIME_13MS, TSL2561_INTEGRATIONTIME_101MS, TSL2561_INTEGRATIONTIME_402MS]:
            raise ValueError('Unexpected integration time value {0}. Set to one of TSL2561_INTEGRATIONTIME_13MS, TSL2561_INTEGRATIONTIME_101MS, TSL2561_INTEGRATIONTIME_402MS'.format(itime))

        self._enable()

        self._device.write8(TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, self._gain | itime)
        self._integration_time = itime

        self._disable()

    def set_gain(self, gain):
        if gain not in [TSL2561_GAIN_1x, TSL2561_GAIN_16x]:
            raise ValueError('Unexpected gain value {0}. Set to one of TSL2561_GAIN_1x, TSL2561_GAIN_16x'.format(gain))

        self._enable()

        self._device.write8(TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, self._integration_time | gain)
        self._gain = gain

        self._disable()

    def read_lux(self):

        ch0, ch1 = self.read_raw_luminosity()
        lux = 0.0

        if ch0 == 0:
            return lux

        ch0 = float(ch0)
        ch1 = float(ch1)

        if self._integration_time == 13:
            ch0 /= 0.034
            ch1 /= 0.034
        elif self._integration_time == 101:
            ch0 /= 0.252
            ch1 /= 0.252

        if self._gain == 16:
            ch0 /= 16
            ch1 /= 16

        ratio = ch1 / ch0

        self._logger.debug(' gain={:d}x, integration time={:.2f} ms'.format(self._gain, self._integration_time))
        self._logger.debug(' ch0={:.2f}, ch1={:.2f}, ratio={:.2f}'.format(ch0, ch1, ratio))

        if self._package & 0x10:
            if 0 < ratio <= 0.52:
                lux = 0.0315 * ch0 - 0.0593 * ch0 * (ratio ** 1.4)
            elif 0.52 < ratio <= 0.65:
                lux = 0.0229 * ch0 - 0.0291 * ch1
            elif 0.65 < ratio <= 0.80:
                lux = 0.0157 * ch0 - 0.0180 * ch1
            elif 0.80 < ratio <= 1.30:
                lux = 0.00338 * ch0 - 0.00260 * ch1
            elif ratio > 1.30:
                lux = 0.0
        else:
            if 0 < ratio <= 0.5:
                lux = 0.0304 * ch0 - 0.062 * ch0 * (ratio ** 1.4)
            elif 0.5 < ratio <= 0.61:
                lux = 0.0224 * ch0 - 0.031 * ch1
            elif 0.61 < ratio <= 0.80:
                lux = 0.0128 * ch0 - 0.0153 * ch1
            elif 0.80 < ratio <= 1.30:
                lux = 0.00146 * ch0 - 0.00112 * ch1
            elif ratio > 1.30:
                lux = 0.0

        return lux
