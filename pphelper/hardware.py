"""
Provides interfaces to laboratory hardware.

"""
from __future__ import division, unicode_literals

import nidaqmx
import numpy as np
import threading
import psychopy.core
import socket


class _StimulationApparatus(object):
    """
    Stimulation apparatus base class.

    Attributes
    ----------
    stimulus : dict
    stimuli : list of dicts

    """
    def __init__(self):
        super(_StimulationApparatus, self).__init__()
        self._stimuli = list()
        self._stimulus = None

    @staticmethod
    def _create_stimulus_from_kwargs(**kwargs):
        replace = kwargs.pop('replace', False)
        stimulus = kwargs
        if 'name' not in stimulus.keys():
            raise KeyError('Please specify a `name` keyword.')
        return stimulus, replace

    def _stimulus_name_exists(self, name):
        return any([stimulus['name'] == name for stimulus in
                    self._stimuli])

    def _stimulus_selected(self):
        return False if self._stimulus is None else True

    def add_stimulus(self, **kwargs):
        """
        Add a new stimulus to the stimulus list or replace an existing one.

        Parameters
        ----------
        stimulus : dict
            A dictionary specifying the stimulus properties. Must contain
            at least a `name` key.

        replace : bool, optional
            Whether an already existing stimulus of the same name should
            be replaced or not. Defaults to ``False``.

        """
        stimulus, replace = self._create_stimulus_from_kwargs(**kwargs)

        if self._stimulus_name_exists(stimulus['name']):
            if replace:
                self.remove_stimulus(stimulus['name'])
            else:
                raise KeyError('Specified stimulus name ``%s`` already '
                               'exists. If you want to replace this '
                               'stimulus, set ``replace=True``.'
                               % stimulus['name'])

        self._stimuli.append(stimulus)

    def select_stimulus(self, name):
        """
        Select the specified stimulus for the next stimulation.

        Parameters
        ----------
        name : string
            The unique name of the stimulus to select.

        """
        if not self._stimulus_name_exists(name):
            raise KeyError('Specified stimulus name ``%s`` does not '
                           'exist. You can add stimuli using '
                           '`add_stimulus()`.' % name)

        # Locate the specified stimulus within the stimulus list and
        # declare it to be the currently selected stimulus.
        for stimulus_n, stimulus in enumerate(self._stimuli):
            if stimulus['name'] == name:
                # We create an explicit copy of the stimulus, so
                # that modifications to the currently selected
                # stimulus are not transferred to self._stimuli.
                self._stimulus = dict(self._stimuli[stimulus_n])
                break
        # Based on http://stackoverflow.com/a/8653568
        # self._stimulus = (stimulus for stimulus in self._stimuli
        #                  if stimulus['name'] == name).next()

    def remove_stimulus(self, name):
        """
        Remove the specified stimulus, identified by its unique name,
        from the stimulus list.
        
        Parameters
        ----------
        name : string
            The unique name of the stimulus to remove.
        
        """
        if not self._stimulus_name_exists(name):
            raise KeyError('Specified stimulus name ``%s`` does not '
                           'exist. You can add stimuli using '
                           '``_add_stimulus()``.' % name)

        # Search through the stimulus list, looking for a stimulus with
        # the specified name. If we get a match, remove the stimulus from
        # the list.
        for stimulus_n, stimulus in enumerate(self._stimuli):
            if stimulus['name'] == name:
                self._stimuli.pop(stimulus_n)
                break

        # Based on http://stackoverflow.com/a/8653568
        # (self._stimuli.pop(stimulus_n) for
        #  stimulus_n, stimulus in enumerate(self._stimuli)
        #  if stimulus['name'] == name).next()

    def stimulate(self, **kwargs):
        raise NotImplementedError('stimulate() not implemented.')

    # Declare some properties with getters and setters for convenient
    # access to those properties.

    # Property `stimulus`.
    @property
    def stimulus(self):
        """
        The currently selected stimulus.

        This stimulus will be presented when invoking ``stimulate``.
        It can be set using ``select_stimulus``.

        See Also
        --------
        select_stimulus, stimulate

        """
        return self._stimulus

    @stimulus.setter
    def stimulus(self, name):
        self.select_stimulus(name)

    @stimulus.deleter
    def stimulus(self):
        self._stimulus = None

    # Property `stimuli`.
    #
    # We do not create a setter. The user should call add_stimulus()
    # instead.
    @property
    def stimuli(self):
        """
        A list of all stimuli added to this stimulation apparatus.

        See Also
        --------
        add_stimulus, remove_stimulus

        """
        return self._stimuli

    @stimuli.deleter
    def stimuli(self):
        del self.stimulus
        self._stimuli = list()


class Olfactometer(_StimulationApparatus):
    """
    Provides an interface to the ValveLink devices used to control
    olfactometers.

    """
    def __init__(self, ni_lines='Dev1/port0/line0:7',
                 ni_trigger_line=None,
                 ni_task_name='Olfactometer',
                 use_threads=True):
        """
        Parameters
        ----------
        ni_lines : string, optional
            The lines of the NI board to use as output channel.
            Defaults to ``Dev1/line0:7``.
        ni_trigger_line : string, optional
            A line on which to generate an additional trigger pulse as the
            olfactometer stimulation is initiated. This can be used to
            start the acquisition of PID data, for example.
        ni_task_name : string, optional
            The name of the NI DAQ task to create.
            Defaults to ``Olfactometer``.
        use_threads : bool, optional
            Whether a Python thread should be created when
            `select_stimulus` is called. This thread would then allow
            non-blocking stimulation.
            Defaults to ``True``.

        """
        super(Olfactometer, self).__init__()
        self._ni_task = nidaqmx.DigitalOutputTask(name=ni_task_name)

        # Add the stimulation channels.
        if not self._ni_task.create_channel(ni_lines):
            raise IOError('Could not create digital output task.')

        self._ni_task_number_of_channels = \
            self._ni_task.get_number_of_channels()

        # Add the trigger channel, if any.
        if ni_trigger_line is None:
            self._ni_task_number_of_trigger_channels = 0
        else:
            if not self._ni_task.create_channel(ni_trigger_line):
                raise IOError('Could not create digital output task.')

            # To get the total number of trigger channels, we subtract
            # the number of channels BEFORE adding the trigger channels
            # from the number of channels AFTER adding the trigger
            # channels.
            self._ni_task_number_of_trigger_channels = \
                self._ni_task.get_number_of_channels() - \
                self._ni_task_number_of_channels

        if not self._ni_task.start():
            raise IOError('Could not start digital output task.')

        self._use_threads = use_threads
        self._thread = None

    def __del__(self):
        self._ni_task.clear()
        del self

    def add_stimulus(self, name, bitmask, duration=1,
                     bitmask_offset=None, onset_delay=0,
                     replace=False, **kwargs):
        """
        Add a stimulus to the stimulus set of this apparatus.

        Parameters
        ----------
        name : string
            A unique identifier of the stimulus to add.
        bitmask : array_like
            The bitmask specifying the valve positions required to present
            this stimulus.
        duration : float, optional
            The duration of the stimulation, specified in seconds.
            Defaults to 1 second.
        bitmask_offset : array_like, optional
            The bitmask specifying the valve positions after the
            stimulation has finished. If not specified, all valves will be
            closed at the end of the stimulation.
        onset_delay : float, optional
            How long to wait after invocation of the ``stimulate``
            method before actually sending the triggers.
            This onset delay can for example be used to align the timing
            of an olfactory stimulus with the onset of a visual stimulus on
            a computer display, which operates at a fixed refresh rate.
        replace : bool, optional
            Whether an already existing stimulus of the same name should
            be replaced or not. Defaults to ``False``.

        Notes
        -----
        Any additional keyword arguments will be added as additional
        stimulus properties.

        See Also
        --------
        remove_stimulus
        stimulate

        """
        bitmask = np.array(bitmask)
        if bitmask.shape[0] != self._ni_task_number_of_channels:
            raise ValueError('Shape of the bitmask does not match number '
                             'of physical lines.')

        if bitmask_offset is None:
            bitmask_offset = np.zeros(self._ni_task_number_of_channels)
        else:
            bitmask_offset = np.array(bitmask_offset)
            if bitmask_offset.shape[0] != self._ni_task_number_of_channels:
                raise ValueError('Please specify a valid bitmask_offset.')

        super(Olfactometer, self).add_stimulus(
            name=name, bitmask=bitmask, bitmask_offset=bitmask_offset,
            duration=duration, onset_delay=onset_delay, replace=replace,
            **kwargs
        )

    def select_stimulus(self, name):
        """
        Select the specified stimulus for the next stimulation.

        Parameters
        ----------
        name : string
            The unique name of the stimulus to select.

        """
        super(Olfactometer, self).select_stimulus(name)

        # Add trigger channel if necessary.
        if self._ni_task_number_of_trigger_channels > 0:
            self._stimulus['bitmask'] = \
                np.r_[self._stimulus['bitmask'],
                      np.repeat(1,
                                self._ni_task_number_of_trigger_channels)]
            self._stimulus['bitmask_offset'] = \
                np.r_[self._stimulus['bitmask_offset'],
                      np.repeat(0,
                                self._ni_task_number_of_trigger_channels)]

        if self._use_threads:
            self._thread = threading.Thread(target=self._stimulate)

    def stimulate(self, blocking_wait=False):
        """
        Start the stimulation with the currently selected stimulus.

        The trigger pulse will open the valves. They are then left open for
        the intended duration of the stimulus. After that, they will be
        switched to the offset state specified by the stimulus.

        Parameters
        ----------
        blocking_wait : bool, optional
            Specifies whether the stimulation thread should be `joined` or
            not, i.e. whether we should wait for it to finish (blocking
            other operations), or return immediately. This parameter will
            be ignored if threads are not used for stimulation.
            Defaults to `False`, i.e. non-blocking behavior.

        See Also
        --------
        add_stimulus
        select_stimulus

        Notes
        -----
        When using thrads, the thread object created by
        ``select_stimulus`` is started when ``stimulate`` is invoked. It
        has to be re-created by calling ``select_stimulus`` before
        ``stimulate`` can be invoked again.

        """
        if self._use_threads:
            self._thread.start()
            if blocking_wait:
                self._thread.join()
        else:
            self._stimulate()

        self._stimulus = None

    def _stimulate(self):
        t0 = psychopy.core.getTime()

        if not self._stimulus_selected():
            raise ValueError('No stimulus selected. Please invoke '
                             '``select_stimulus()`` first.')

        stimulus_duration = self._stimulus['duration']
        onset_delay = self._stimulus['onset_delay']
        bitmask = self._stimulus['bitmask']
        bitmask_offset = self._stimulus['bitmask_offset']

        if onset_delay > 0:
            onset_wait = onset_delay - (psychopy.core.getTime() - t0)
            psychopy.core.wait(onset_wait, hogCPUperiod=onset_wait/5)

        if self._ni_task.write(bitmask) <= 0:
            raise IOError('Could not write onset bitmask.')

        psychopy.core.wait(stimulus_duration,
                           hogCPUperiod=stimulus_duration/5)

        if self._ni_task.write(bitmask_offset) <= 0:
            raise IOError('Could not write offset bitmask.')


class AnalogInput(object):
    """
    Analog data acquisition using a National Instruments board.

    """
    def __init__(self, ni_input_line='Dev1/ai0',
                 ni_trigger_line=None,
                 sampling_duration=3,
                 sampling_rate=2000,
                 ni_task_name='AnalogInput'):

        """
        Parameters
        ----------
        ni_input_line : str, optional
            The analog input line to acquire the data from.
            Defaults to `Dev1/ai0`.
        ni_trigger_line : str, optional
            If specified, start the acquisition only after a start trigger
            (high voltage) on this line has been received.
            If `None`, no external trigger is required.
        sampling_duration : float, optional
            How long to sample, specified in seconds.
            Defaults to 3 seconds.
        sampling_rate : int, optional
            At which rate (in Hz) to sample the analog input signal.
            Defaults to 2000 Hz.
        ni_task_name : str, optional
            The name of the NIDAQmx task to create.
            Defaults to `AnalogInput`.

        """
        self._sampling_duration = sampling_duration
        self._sampling_rate = sampling_rate
        self._samples_to_acquire = self._sampling_rate * \
                                   self._sampling_duration

        self._ni_task = nidaqmx.AnalogInputTask(name=ni_task_name)
        if not self._ni_task.create_voltage_channel(
                ni_input_line, min_val=-10, max_val=10):
            raise IOError('Could not create analog input channel.')

        if not self._ni_task.configure_timing_sample_clock(
                rate=self._sampling_rate,
                sample_mode='finite',
                samples_per_channel=self._samples_to_acquire):
            raise IOError('Could not configure analog input sample clock.')

        self._ni_task_number_of_channels = \
            self._ni_task.get_number_of_channels()

        if ni_trigger_line is None:
            self._ni_task_number_of_trigger_channels = 0
        else:
            if not self._ni_task.configure_trigger_digital_edge_start(
                    ni_trigger_line):
                raise IOError('Could not configure trigger channel.')

            self._ni_task_number_of_trigger_channels = 1

            # Data acquisition is set to be triggered by an external
            # trigger. Thus we can start the task immediately.
            if not self._ni_task.start():
                raise IOError('Could not start analog input task.')

    def __del__(self):
        self._ni_task.clear()
        del self

    def get_data(self):
        """
        Return the acquired data.

        If the acquisition is not finished by the time this method is
        called, it will first wait until finished (blocking other
        processing) and then return the data.

        """
        # If we do not use an external trigger, start the data
        # acquisition immediately.
        if self._ni_task_number_of_trigger_channels == 0:
            self._ni_task.start()

        self._ni_task.wait_until_done()
        read = self._ni_task.read(timeout=-1)
        self._ni_task.stop()

        # If we use an external trigger, we need to re-start the task, or
        # else the next acquisition won't work because the task would be
        # still stopped.
        if self._ni_task_number_of_trigger_channels > 0:
            self._ni_task.start()

        return read

    trigger = get_data

    @property
    def sampling_duration(self):
        """
        The duration (in seconds) of data acquisition.

        """
        return self._sampling_duration

    @sampling_duration.setter
    def sampling_duration(self, duration):
        self._ni_task.stop()
        self._sampling_duration = duration
        self._samples_to_acquire = self._sampling_rate * \
                                   self._sampling_duration
        self._ni_task.configure_timing_sample_clock(
            rate=self._sampling_rate,
            sample_mode='finite',
            samples_per_channel=self._samples_to_acquire
        )

        # Only start the task if it is set to be triggered by
        # an external trigger. Otherwise we would start recording
        # immediately.
        if self._ni_task_number_of_trigger_channels > 0:
            self._ni_task.start()

    @property
    def sampling_rate(self):
        """
        The sampling rate (in Hz) of the analog data acquisition.

        """
        return self._sampling_rate

    @sampling_rate.setter
    def sampling_rate(self, sampling_rate):
        self._ni_task.stop()
        self._sampling_rate = sampling_rate
        self._samples_to_acquire = self._sampling_rate * \
                                   self._sampling_duration
        self._ni_task.configure_timing_sample_clock(
            rate=sampling_rate,
            sample_mode='finite',
            samples_per_channel=self._samples_to_acquire
        )

        # Only start the task if it is set to be triggered by
        # an external trigger. Otherwise we would start recording
        # immediately.
        if self._ni_task_number_of_trigger_channels > 0:
            self._ni_task.start()

    @property
    def samples_to_acquire(self):
        """
        The number of samples to acquire in the acquisition. This is the
        product of the sampling rate and the sampling duration.

        """
        return self._samples_to_acquire


class Gustometer(_StimulationApparatus):
        """
        Provide an interface to the Burghart GU002 gustometer.

        """
        def __init__(self, pulse_duration=0.1, pause_duration=0.2,
                     gusto_ip='192.168.0.1', gusto_port=40175,
                     local_ip='192.168.0.10', local_port=40176,
                     ni_trigger_out_line='Dev1/PFI1',
                     ni_trigger_in_line='Dev1/ctr0',
                     ni_trigger_out_task_name='GustometerOut',
                     ni_trigger_in_task_name='GustometerIn'):
            """
            Parameters
            ----------
            cycle_duration : float
                The duration of one stimulation cycle, in seconds.

            ni_trigger_out_line : string
                The digital output line on the NI board which shall be used to
                send the trigger to the gustometer.

            ni_trigger_in_line : string
                The counter input line on the NI board which shall be used to
                receive the trigger pulse emitted by the gustometer as soon
                presentation of the requested stimulus has actually started.

            ni_trigger_out_task_name : string, optional
                The name to assign to the trigger output task.
                Defaults to ``GustometerOut``.

            ni_trigger_in_task_name : string, optional
                The name to assign to the trigger input task.
                Defaults to ``GustometerIn``.

            gusto_ip : string, optional
                The IP address of the gustometer control computer.
                Defaults to ``192.168.0.1``.

            gusto_port : int, optional
                The port on which the control software on the gustometer
                control computer is listening for a connection. This should
                usually not need to be changed.
                Defaults to ``40175``.

            local_ip : string, optional
                The IP address of the computer running the experimental
                scripts. This should be the address of the interface which is
                connected to the gustometer control computer.
                Defaults to ``192.168.0.10``.

            local_port : string, optional
                The port on which to listen for responses from the gustometer
                control computer.
                Defaults to ``40176``.

            """
            super(Gustometer, self).__init__()
            self._pulse_duration = pulse_duration
            self._pause_duration = pause_duration
            self._gusto_ip = gusto_ip
            self._gusto_port = gusto_port
            self._local_ip = local_ip
            self._local_port = local_port
            self._timer = psychopy.core.Clock()
            self._stimuli = list()
            self._stimulus = None

            # Initialize OUT trigger (FROM computer TO gusto).
            # Sending this trigger will cause the gustometer to present the
            # stimulus in the next pulse cycle.
            self._ni_trigger_out_task = nidaqmx.DigitalOutputTask(
                name=ni_trigger_out_task_name
            )
            self._ni_trigger_out_task.create_channel(ni_trigger_out_line)
            self._ni_trigger_out_task.start()

            # Initialize IN trigger (FROM gusto TO computer).
            # The gustometer will send this trigger as soon as the stimulus
            # presentation has started.
            self._ni_trigger_in_task = nidaqmx.CounterInputTask(
                name=ni_trigger_in_task_name
            )
            self._ni_trigger_in_task.create_channel_count_edges(
                ni_trigger_in_line,
                edge='rising',
                direction='up',
                init=0
            )
            self._ni_trigger_in_task.start()

            # Initialize the network connection.
            self._socket_send = socket.socket(socket.AF_INET,  # IP
                                              socket.SOCK_DGRAM)  # UDP

            self._socket_receive = socket.socket(socket.AF_INET,  # IP
                                                 socket.SOCK_DGRAM)  # UDP

            self._socket_receive.bind((self._local_ip, self._local_port))
            self._socket_receive.settimeout(0.1)
            self._connect()

        def _send(self, message):
            self._socket_send.sendto(message, (self._gusto_ip,
                                               self._gusto_port))

        def _connect(self):
            message = 'CONNECT %s 0' % self._local_port

            # # Empty receive buffer.
            # self._socket_receive.setblocking(False)
            # for ............

            self._send(message)

        def add_stimulus(self, name, classnum, replace=False, **kwargs):
            """
            Add a stimulus to the stimulus set of this apparatus.

            Parameters
            ----------
            name : string
                A unique identifier of the stimulus to add.
            classnum : int
                The stimulus class number, as defined in the Gusto Control
                Software.
            replace : bool, optional
                Whether an already existing stimulus of the same name should
                be replaced or not. Defaults to ``False``.

            Notes
            -----
            Any additional keyword arguments will be added as additional
            stimulus properties.

            See Also
            --------
            remove_stimulus
            stimulate

            """
            super(Gustometer, self).add_stimulus(
                name=name, classnum=classnum, replace=replace, **kwargs
            )

        def select_stimulus(self, name):
            super(Gustometer, self).select_stimulus(name)
            message = 'CLASSNUM %d 0' % self._stimulus['classnum']
            self._send(message)

        def stimulate(self):
            if not self._stimulus_selected():
                raise ValueError('No stimulus selected. Please invoke '
                                 '``select_stimulus()`` first.')

            # # Set trigger line to HIGH.
            # if self._ni_task.write(self._ni_trigger_out_task.write(1)) <= 0:
            #     raise IOError('Could not write send trigger.')
            #
            # psychopy.core.wait(0.010)
            #
            # # Set trigger line to LOW again.
            # if self._ni_task.write(self._ni_trigger_out_task.write(0)) <= 0:
            #     raise IOError('Could not write send trigger.')

            message = 'TRIGSTART 1 1'
            self._send(message)
            self._stimulus = None

        def trigger_conf(self, duration=0.9, int_taste=100, int_bg=100):
            """
            Configure the trigger on the gusto.

            Parameters
            ----------
            duration : int, optional
                Trigger duration (stimulation duration) in seconds.
                Defaults to 0.9s.
            int_taste : int
                Taste intensity in percent.
                Defaults to 100%.
            int_bg : int
                Background intensity in percent.
                Defaults to 100%.

            """
            message = 'TRIGCONF %d %d %d' % (duration*1000,
                                             int_taste, int_bg)
            self._send(message)
