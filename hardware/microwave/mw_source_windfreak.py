import visa
import numpy as np
import time 

from core.module import Base, ConfigOption
from interface.microwave_interface import MicrowaveInterface
from interface.microwave_interface import MicrowaveLimits
from interface.microwave_interface import MicrowaveMode
from interface.microwave_interface import TriggerEdge

class MicrowaveWindfreak(Base, MicrowaveInterface):
    """ This is the Interface class to define the controls for the simple
        microwave hardware.
    """

    _modclass = 'MicrowaveWindfreak'
    _modtype = 'hardware'

    _usb_address = ConfigOption('usb_address', missing='error')
    _usb_timeout = ConfigOption('usb_timeout', 10, missing='warn')

    _internal_mode = 'cw'

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._usb_timeout = self._usb_timeout * 1000
        # trying to load the visa connection to the module
        self.rm = visa.ResourceManager()
        self._usb_connection = self.rm.open_resource(
            resource_name=self._usb_address,
            timeout=self._usb_timeout)

        self.log.info('MWWINDFREAK initialised and connected to hardware.')
        self.model = self._usb_connection.query('+')

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """

        self._usb_connection.close()
        self.rm.close()

    def get_limits(self):
        limits = MicrowaveLimits()
        limits.supported_modes = (MicrowaveMode.CW, MicrowaveMode.LIST, MicrowaveMode.SWEEP)

        limits.min_frequency = 54e6
        limits.max_frequency = 13.6e9

        limits.min_power = -50
        limits.max_power = 20

        limits.list_minstep = 0.1
        limits.list_maxstep = 13.5e9
        limits.list_maxentries = 100

        limits.sweep_minstep = 0.1
        limits.sweep_maxstep = 13.5e9
        limits.sweep_maxentries = 10001
        return limits

    def on(self):
        """ Switches on any preconfigured microwave output.

        @return int: error code (0:OK, -1:error)
        """

        self._usb_connection.write('E1r1')

        return 0

    def off(self):
        """ Switches off any microwave output.

        @return int: error code (0:OK, -1:error)
        """
        self._usb_connection.write('E0r0')

        return 0  
    @property

    def get_status(self):
        """ Get the current status of the MW source, i.e. the mode
        (cw, list or sweep) and the output state (stopped, running).

        @return str, bool: mode ['cw', 'list', 'sweep'], is_running [True, False]
        """
        internal_mode="sweep"
        is_running = bool(int(self._usb_connection.query('r?').strip()))
        return internal_mode, is_running

    def get_power(self):
        """ Gets the microwave output power.

        @return float: the power set at the device in dBm
        """
        return float(self._usb_connection.write('W?'))

    def set_power(self, power=0.):
        """ Sets the microwave output power.

        @param float power: the power (in dBm) set for this device

        @return int: error code (0:OK, -1:error)
        """
        if power is not None:
            self._usb_connection.write('W{0:f}'.format(power))
            return 0
        else:
            return -1

    def get_frequency(self):
        """ Gets the frequency of the microwave output.

        @return float: frequency (in Hz), which is currently set for this device
        """
        return float(self._usb_connection.query('f?'))

    def set_frequency(self, freq=None):
        """ Sets the frequency of the microwave output.

        @param float freq: the frequency (in Hz) set for this device

        @return int: error code (0:OK, -1:error)
        """
        if freq is not None:
            self._usb_connection.write('f{0:e} MHz'.format(freq))
            return 0
        else:
            return -1
    def cw_on(self):
        """ Switches on cw microwave output.

        @return int: error code (0:OK, -1:error)

        Must return AFTER the device is actually running.
        """
        is_running = self.get_status()
        self.internal_mode = 'cw'
        if is_running:
            if self.internal_mode == 'cw':
                return 0
            else:
                self.off()

        if self.internal_mode != 'cw':
            self._usb_connection.write('E1e1')

        self.__usb_connection.write('E1e1')
        is_running = self.get_status()
        self.internal_mode = 'cw'

        while not is_running:
            time.sleep(0.2)
            internal_mode, is_running = self.get_status()
        return 0
    def set_cw(self, frequency=None, power=None):

        is_running = self.get_status()
        self.internal_mode = "cw"

        if is_running:
            self.off()

        # Activate CW mode
        if self.internal_mode != 'cw':
            self._usb_connection.write('E1r1')

        # Set CW frequency
        if frequency is not None:
            self._usb_connection.write('f{0:f}'.format(frequency))

        # Set CW power
        if power is not None:
            self._usb_connection.write('W{0:f}'.format(power))

        # Return actually set values

        self.internal_mode, is_running = self.get_status()

        actual_freq = self.get_frequency()
        actual_power = self.get_power()
        return actual_freq, actual_power, self.internal_mode

    def set_list(self, freq=None, power=None):
        """ There is no list mode for agilent
        # Also the list is created by giving 'start_freq, step, stop_freq'

        @param list freq: list of frequencies in Hz
        @param float power: MW power of the frequency list in dBm

        """
#        if self.set_cw(freq[0],power) != 0:
#            error = -1

        #self._usb_connection.write(':SWE:RF:STAT ON')

        # put all frequencies into a string, first element is doubled
        # so there are n+1 list entries for scanning n frequencies
        # due to counter/trigger issues
        #freqstring = ' {0:f},'.format(freq[0])
        #for f in freq[:-1]:
        #    freqstring += ' {0:f},'.format(f)
        #freqstring += ' {0:f}'.format(freq[-1])

        #freqcommand = ':LIST:FREQ' + freqstring

        n = len(freq)
        self._usb_connection.write('X0')
        self._usb_connection.write('l{0:e}'.format(freq[0]))
        self._usb_connection.write('u{0:e}'.format(freq[-1]))
        self._usb_connection.write('s{0}'.format(n))
        self._usb_connection.write('t10.00')
       

        self._usb_connection.write('[{0:f}'.format(power))
        self._usb_connection.write(']{0:f}'.format(power))
        self._usb_connection.write('^1')

        self._usb_connection.write('g1')
        self.internal_mode = 'list'

        return 0

    def reset_listpos(self):
        """ Reset of MW List Mode position to start from first given frequency

        @return int: error code (0:OK, -1:error)
        """
        self._usb_connection.write('g0')
        return 0
    def reset_sweeppos(self):
        """
        Reset of MW sweep mode position to start (start frequency)

        @return int: error code (0:OK, -1:error)

        """
        self.internal_mode = 'sweep'
        self._usb_connection.write('g1')
        return 0		
    def set_sweep(self, start, stop, step, power):
        """

        @param start:
        @param stop:
        @param step:
        @param power:
        @return:
        """
        #self._usb_connection.write(':SOUR:POW ' + str(power))
        #self._usb_connection.write('*WAI')

        self._gpib_connection.write('X0')
        self._gpib_connection.write('l' + str(start-step))
        self._gpib_connection.write('u' + str(stop))
        self._gpib_connection.write('s' + str(step))
        self._gpib_connection.write('x2') #ustawione tymczasowo triggerowanie wewnetrzene 10 MHz
        self._gpib_connection.write('w1')
        self.internal_mode = 'sweep'
        
        return self.internal_mode

    def reset_sweep(self):
        """ Reset of MW List Mode position to start from first given frequency

        @return int: error code (0:OK, -1:error)
        """
        self._usb_connection.write('g1')
        self._usb_connection.write('g0')
        return 0

    def sweep_on(self):
        """ Switches on the list mode.

        @return int: error code (1: ready, 0:not ready, -1:error)
        """
        self._usb_connection.write('E1r1')
        self._usb_connection.write('g1')  
        self.internal_mode = 'sweep'
        return 1

    def list_on(self):
        """ Switches on the list mode.

        @return int: error code (1: ready, 0:not ready, -1:error)
        """
        self.internal_mode = 'list'
        self._usb_connection.write('e1r1')
        self._usb_connection.write('g1')


        return 0

    def set_ext_trigger(self, pol=TriggerEdge.RISING):
        """ Set the external trigger for this device with proper polarization.

        @param str source: channel name, where external trigger is expected.
        @param str pol: polarisation of the trigger (basically rising edge or
                        falling edge)

        @return int: error code (0:OK, -1:error)
        """
        if pol == TriggerEdge.RISING:
            edge = 'w1'
        elif pol == TriggerEdge.FALLING:
            edge = 'w1'
        else:
            return -1
        try:
            self._usb_connection.write('{0}'.format(edge))
        except:
            return -1
        return 0
