"""
Provides interfaces to laboratory hardware.

"""
from __future__ import division, unicode_literals

import nidaqmx
import numpy as np
import threading
import psychopy.core
import socket
import time


class _StimulationApparatus(object):
    """
    Stimulation apparatus base class.

    Attributes
    ----------
    stimulus : dict
    stimuli : list of dicts
    test_mode : bool

    """
    def __init__(self, test_mode=False):
        super(_StimulationApparatus, self).__init__()
        self._stimuli = list()
        self._stimulus = None
        self._test_mode = test_mode

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

    @property
    def test_mode(self):
        return self._test_mode

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
                 use_threads=True,
                 test_mode=False):
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
        test_mode : bool, optional
            If ``True``, the NI board will not actually be initialized or used
            in any manner. This allows for testing the program logic on a
            computer without a DAQ card.
            Defaults to ``False``.

        """
        super(Olfactometer, self).__init__(test_mode=test_mode)

        if not self.test_mode:
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
        else:
            self._ni_task_number_of_channels = 8
            self._ni_task_number_of_trigger_channels = 1

        self._use_threads = use_threads
        self._thread = None

    def __del__(self):
        if not self.test_mode:
            self._ni_task.clear()
        del self

    def add_stimulus(self, name, bitmask, duration=1,
                     bitmask_offset=None, trigger_time=None,
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
        trigger_time : float, optional
            The time (in terms of the ``psychopy.core.getTime`` timebase)
            at which the stimulation should be triggered. If ``None``,
            trigger immediately.
            Defaults to ``None``.
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
        select_stimulus
        stimulate

        """
        bitmask = np.array(bitmask, dtype=np.uint8)
        if bitmask.shape[0] != self._ni_task_number_of_channels:
            raise ValueError('Shape of the bitmask does not match number '
                             'of physical lines.')

        if bitmask_offset is None:
            bitmask_offset = np.zeros(
                self._ni_task_number_of_channels,
                dtype=np.uint8
            )
        else:
            bitmask_offset = np.array(bitmask_offset, dtype=np.uint8)
            if bitmask_offset.shape[0] != self._ni_task_number_of_channels:
                raise ValueError('Please specify a valid bitmask_offset.')

        super(Olfactometer, self).add_stimulus(
            name=name, bitmask=bitmask, bitmask_offset=bitmask_offset,
            duration=duration, trigger_time=trigger_time,
            replace=replace, **kwargs
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
        ``stimulate`` invokes ``_stimulate``, which itself unsets the
        currently selected stimulus at the end of the stimulation. You have
        to invoke ``select_stimulus`` again before you can call
        ``stimulate`` again.

        """
        if not self._stimulus:
            raise ValueError('No stimulus selected. Please invoke '
                             '``select_stimulus()`` first.')

        if self._use_threads:
            self._thread.start()
            if blocking_wait:
                self._thread.join()
        else:
            self._stimulate()

    def _stimulate(self):
        stimulus_duration = self._stimulus['duration']
        bitmask = self._stimulus['bitmask']
        bitmask_offset = self._stimulus['bitmask_offset']
        trigger_time = self._stimulus['trigger_time']

        if trigger_time is not None:
            if psychopy.core.getTime() < trigger_time:
                psychopy.core.wait(
                    trigger_time - psychopy.core.getTime(),
                    hogCPUperiod=(trigger_time - psychopy.core.getTime()) / 5
                )

        if not self.test_mode:
            if self._ni_task.write(bitmask) <= 0:
                raise IOError('Could not write onset bitmask.')

        psychopy.core.wait(stimulus_duration,
                           hogCPUperiod=stimulus_duration/5)

        if not self.test_mode:
            if self._ni_task.write(bitmask_offset) <= 0:
                raise IOError('Could not write offset bitmask.')

        self._stimulus = None


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
        self._samples_to_acquire = int(np.floor(self._sampling_rate * \
                                                self._sampling_duration))

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
        if not self.test_mode:
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
        self._samples_to_acquire = \
            np.ceil(self._sampling_rate * self._sampling_duration)
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
                 ni_trigger_in_line='PFI14',
                 ni_trigger_in_task_name='GustometerIn',
                 use_threads=False,
                 test_mode=False):
        """
        Parameters
        ----------
        pulse_duration : float, optional
            The duration of one stimulation pulse, in seconds.
            Defaults to 0.1.
        pause_duration : float, optional
            The duration of the spray pause between two pulses in seconds.
            Defaults to 0.2
        gusto_ip : string, optional
            The IP address of the gustometer control computer.
            Defaults to ``192.168.0.1``.
        gusto_port : int, optional
            The port on which the control software on the gustometer
            control computer is listening for a connection. This should
            usually not need to be changed.
            Defaults to ``40175``.
        ni_trigger_in_line : string, optional
            The counter input line on the NI board which shall be used to
            receive the trigger pulse emitted by the gustometer as soon
            presentation of the requested stimulus has actually started.
            Defaults to ``Dev1/ctr0``.
        ni_trigger_in_task_name : string, optional
            The name to assign to the trigger input task.
            Defaults to ``GustometerIn``.
        use_threads : bool, optional
            Whether a Python thread should be created when
            `select_stimulus` is called. This thread would then allow
            non-blocking stimulation.
            Defaults to ``False``.
        test_mode : bool, optional
            If ``True``, the NI board will not actually be initialized or used
            in any manner. This allows for testing the program logic on a
            computer without a DAQ card.
            Defaults to ``False``.

        """
        super(Gustometer, self).__init__(test_mode=test_mode)
        self._pulse_duration = pulse_duration
        self._pause_duration = pause_duration
        self._classfile = None
        self._gusto_ip = gusto_ip
        self._gusto_port = gusto_port
        self._use_threads = use_threads
        self._thread = None
        # FIXME add parameter to docs.

        if not self.test_mode:
            # Initialize IN trigger (FROM gusto TO computer).
            # The gustometer will send this trigger as soon as the stimulus
            # presentation has started.
            # self._ni_trigger_in_task = nidaqmx.DigitalInputTask(
            #     name=ni_trigger_in_task_name
            # )
            #
            # self._ni_trigger_in_task.create_channel(
            #     ni_trigger_in_line
            # )
            #
            # self._ni_trigger_in_task.configure_timing_change_detection(
            #     rising_edge_channel=ni_trigger_in_line,
            #     sample_mode='finite',
            #     samples_per_channel=1
            # )
            #
            self._ni_ai_task = nidaqmx.AnalogInputTask(name=ni_trigger_in_task_name)
            if not self._ni_ai_task.create_voltage_channel(
                    'Dev1/ai0', min_val=-10, max_val=10):
                raise IOError('Could not create analog input channel.')

            if not self._ni_ai_task.configure_timing_sample_clock(
                    rate=192000,
                    sample_mode='finite',
                    samples_per_channel=2):
                raise IOError('Could not configure analog input sample clock.')

            if not self._ni_ai_task.configure_trigger_digital_edge_start(
                    ni_trigger_in_line):
                raise IOError('Could not configure trigger channel.')

            # self._ni_trigger_in_task.create_channel_count_edges(
            #     ni_trigger_in_line,
            #     edge='rising',
            #     direction='up',
            #     init=0
            # )

        # Initialize the network connection.
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(1)

        try:
            self._socket.connect((self._gusto_ip, self._gusto_port))
        except socket.error:
            if not self._test_mode:
                msg = ('Could not connect to Gustometer computer at %s:%s!' %
                       (self._gusto_ip, self._gusto_port))
                raise RuntimeError(msg)
            else:
                pass

        self._mode = 'edit'

    def __del__(self):
        if not self.test_mode:
            self._ni_ai_task.clear()
            self._socket.close()

        del self

    def _send(self, message):
        # Append \r\n if it's not already part of the message: GustoControl
        # uses these characters as command separators.
        if not message.endswith('\r\n'):
            message += '\r\n'

        if not self._test_mode:
            self._socket.sendall(message)
        else:
            pass

    def set_mode(self, mode):
        """
        Switch between `edit` `experiment` mode.

        In `edit` mode, the background stimulus presentation is off. In
        `experiment` mode, the background stimulus presentation is on.

        Parameters
        ----------
        mode : string
            If `edit`, switch to edit mode.
            If `experiment` or `exp`, switch to experiment mode.

        """
        if mode == 'edit':
            mode_num = 1
            self._mode = 'edit'
        elif (mode == 'experiment') or (mode == 'exp'):
            mode_num = 2
            self._mode = 'experiment'
        else:
            raise ValueError('`mode` has to be one of: edit, experiment, exp.')

        message = 'CLASSMODE %d' % mode_num
        self._send(message)

    def trigger_conf(self, duration=0.9, int_taste=100, int_bg=100):
        """
        Configure the trigger on the gusto.

        Parameters
        ----------
        duration : int, optional
            Trigger duration (stimulation duration) in seconds.
            Defaults to 0.9s.
        int_taste : int, optional
            Taste intensity in percent.
            Defaults to 100%.
        int_bg : int, optional
            Background intensity in percent.
            Defaults to 100%.

        """
        message = 'TRIGCONF %d %d %d' % (duration * 1000,
                                         int_taste, int_bg)
        self._send(message)

    def load_classfile(self, filename):
        """
        Load a classes file in the Gusto Control software.

        Parameters
        ----------
        filename : string
            The filename of the classes file to be loaded, including the
            file extension (typically `.cla`).

        """
        message = 'CLASSFILE %s' % filename
        self._send(message)
        self._classfile = filename

    def add_stimulus(self, name, classnum, trigger_time=None,
                     wait_for_gusto_trigger=True, replace=False, **kwargs):
        """
        Add a stimulus to the stimulus set of this apparatus.

        Parameters
        ----------
        name : string
            A unique identifier of the stimulus to add.
        classnum : int
            The stimulus class number, as defined in the Gusto Control
            software.
        wait_for_gusto_trigger : bool, optional
            Whether to block program execution and wait until we receive the
            trigger from the gustometer, informing us about the precise time
            of stimulus onset.
            Defaults to `True`.
        trigger_time : float, optional
            The time (in terms of the ``psychopy.core.getTime`` timebase)
            at which the stimulation should be triggered. If ``None``,
            trigger immediately.
            Defaults to ``None``.
        replace : bool, optional
            Whether an already existing stimulus of the same name should
            be replaced or not. Defaults to ``False``.

        Notes
        -----
        Any additional keyword arguments will be added as additional
        stimulus properties.

        See Also
        --------
        select_stimulus
        remove_stimulus
        stimulate

        """
        classnum = np.uint8(classnum)
        super(Gustometer, self).add_stimulus(
            name=name, classnum=classnum,
            trigger_time=trigger_time,
            wait_for_gusto_trigger=wait_for_gusto_trigger,
            replace=replace, **kwargs
        )

    def select_stimulus(self, name):
        """
        Select the specified stimulus for the next stimulation.

        Parameters
        ----------
        name : string
            The unique name of the stimulus to select.

        """
        super(Gustometer, self).select_stimulus(name)
        message = 'CLASSNUM %d 0' % self._stimulus['classnum']
        self._send(message)

        if not self.test_mode and self._stimulus['wait_for_gusto_trigger']:
            self._ni_ai_task.stop()
            self._ni_ai_task.start()

        if self._use_threads:
            self._thread = threading.Thread(target=self._stimulate)

    def stimulate(self, blocking_wait=False):
        """
        Start the stimulation with the currently selected stimulus.

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
        ``stimulate`` invokes ``_stimulate``, which itself unsets the
        currently selected stimulus at the end of the stimulation. You have
        to invoke ``select_stimulus`` again before you can call
        ``stimulate`` again.
        """
        if not self._stimulus:
            raise ValueError('No stimulus selected. Please invoke '
                             '``select_stimulus()`` first.')

        if self._use_threads:
            self._thread.start()
            if blocking_wait:
                self._thread.join()
        else:
            self._stimulate()

    def _stimulate(self):
        message = 'TRIGSTART 1 1'
        trigger_time = self._stimulus['trigger_time']

        if trigger_time is not None:
            if psychopy.core.getTime() < trigger_time:
                psychopy.core.wait(
                    trigger_time - psychopy.core.getTime(),
                    hogCPUperiod=(
                                 trigger_time - psychopy.core.getTime()) / 5
                )

        self._send(message)
        if not self.test_mode and self._stimulus['wait_for_gusto_trigger']:
            self._ni_ai_task.wait_until_done()
        self._stimulus = None


class Trigger(_StimulationApparatus):
    """
    Send triggers, e.g. to the EEG system.

    """
    def __init__(self, ni_lines='Dev1/PFI2:9',
                 ni_start_trigger_line=None,
                 ni_task_name='Triggers',
                 use_threads=False,
                 test_mode=False):
        """
        Parameters
        ----------
        ni_lines : string, optional
            The lines of the NI board to use as output channel.
            Defaults to ``Dev1/PFI2:9``.
        ni_start_trigger_line : str or None, optional
            If specified, start the generation only after a start trigger
            (high voltage) on this digital line has been received.
            If `None`, no external trigger is required.
        ni_task_name : string, optional
            The name of the NI DAQ task to create.
            Defaults to ``Triggers``.
        use_threads : bool, optional
            Whether a Python thread should be created when
            `select_stimulus` is called. This thread would then allow
            non-blocking stimulation.
            Defaults to ``False``.
        test_mode : bool, optional
            If ``True``, the NI board will not actually be initialized or used
            in any manner. This allows for testing the program logic on a
            computer without a DAQ card.
            Defaults to ``False``.

        """
        super(Trigger, self).__init__(test_mode=test_mode)
        if not self.test_mode:
            self._ni_task = nidaqmx.DigitalOutputTask(name=ni_task_name)

            # Add the trigger channels.
            if not self._ni_task.create_channel(ni_lines):
                raise IOError('Could not create digital output task.')

            self._ni_task_number_of_channels = \
                self._ni_task.get_number_of_channels()


            # if not self._ni_task.configure_timing_sample_clock(
            #         rate=self._sampling_rate,
            #         sample_mode='finite',
            #         samples_per_channel=self._samples_to_acquire):
            #     raise IOError('Could not configure analog input sample clock.')

            if ni_start_trigger_line is not None:
                if not self._ni_task.configure_trigger_digital_edge_start(
                        ni_start_trigger_line):
                    raise IOError('Could not configure trigger channel.')

                # Data generation is set to be triggered by an external
                # trigger. Thus we can start the task immediately.
                if not self._ni_task.start():
                    raise IOError('Could not start digital output task.')
        else:
            self._ni_task_number_of_channels = 8

        self._use_threads = use_threads
        self._thread = None

    def __del__(self):
        if not self.test_mode:
            self._ni_task.clear()
        del self

    def add_stimulus(self, *args, **kwargs):
        self.add_trigger(*args, **kwargs)

    def add_trigger(self, name, trig_num, duration=None, trigger_time=None,
                    replace=False, **kwargs):
        """
        Add a stimulus to the stimulus set of this apparatus.

        Parameters
        ----------
        name : string
            A unique identifier of the stimulus to add.
        trig_num : int
            The trigger to send.
        duration : float or None, optional
            The duration of the trigger HIGH voltage, specified in seconds.
            Defaults to 0.001 second. If `None`, the trigger line is left in
            the HIGH state.
        trigger_time : float, optional
            The time (in terms of the ``psychopy.core.getTime`` timebase)
            at which the stimulation should be triggered. If ``None``,
            trigger immediately.
            Defaults to ``None``.
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
        select_stimulus
        stimulate

        """
        bits = self._ni_task_number_of_channels
        max_val = 2**bits - 1  # Maximum integer value we can represent with this no. of bits.

        if trig_num > max_val:
            trig_num = max_val

        bitmask = np.array(
            list(bin(trig_num)[2:].zfill(bits))[::-1],  # Most significant bit RIGHT, not left!
            dtype=np.uint8
        )

        super(Trigger, self).add_stimulus(
                name=name, bitmask=bitmask, duration=duration,
                trigger_time=trigger_time, replace=replace, **kwargs
        )

    def select_stimulus(self, name):
        self.select_trigger(name)

    def select_trigger(self, name):
        """
        Select the specified trigger for the next generation.

        Parameters
        ----------
        name : string
            The unique name of the trigger to select.

        """
        super(Trigger, self).select_stimulus(name)

        if self._use_threads:
            self._thread = threading.Thread(target=self._stimulate)

    def remove_trigger(self, name):
        self.remove_stimulus(name)

    def trigger(self, blocking_wait=False):
        self.stimulate(blocking_wait=blocking_wait)

    def stimulate(self, blocking_wait=False):
        """
        Start the generation of the currently selected trigger.

        Parameters
        ----------
        blocking_wait : bool, optional
            Specifies whether the trigger thread should be `joined` or
            not, i.e. whether we should wait for it to finish (blocking
            other operations), or return immediately. This parameter will
            be ignored if threads are not used for stimulation.
            Defaults to `False`, i.e. non-blocking behavior.

        See Also
        --------
        add_trigger
        select_trigger
        add_stimulus
        select_stimulus

        Notes
        -----
        ``trigger`` invokes ``_trigger``, which itself unsets the
        currently selected trigger at the end of the generation. You have
        to invoke ``select_trigger`` again before you can call
        ``trigger`` again.

        """
        if not self._stimulus:
            raise ValueError('No stimulus selected. Please invoke '
                             '``select_stimulus()`` first.')

        if self._use_threads:
            self._thread.start()
            if blocking_wait:
                self._thread.join()
        else:
            self._stimulate()

    def _stimulate(self):
        stimulus_duration = self._stimulus['duration']
        bitmask = self._stimulus['bitmask']
        trigger_time = self._stimulus['trigger_time']

        if trigger_time is not None:
            if psychopy.core.getTime() < trigger_time:
                psychopy.core.wait(
                        trigger_time - psychopy.core.getTime(),
                        hogCPUperiod=(trigger_time - psychopy.core.getTime()) / 5
                )

        if not self.test_mode:
            if self._ni_task.write(bitmask) <= 0:
                raise IOError('Could not write onset bitmask.')

        if stimulus_duration is not None:
            psychopy.core.wait(stimulus_duration,
                               hogCPUperiod=stimulus_duration/5)
            bitmask = np.zeros(self._ni_task_number_of_channels)
            if self._ni_task.write(bitmask) <= 0:
                raise IOError('Could not write offset bitmask.')

        self._stimulus = None


class EEG(object):
    """
    Provides a remote-control interface to PyCorder.

    """
    def __init__(self, exp_name, participant, config_file,
                 pycorder_host='758098-G-PC', pycorder_port=6700,
                 test_mode=False):
        """
        Parameters
        ----------
        exp_name : str
            Name of the experiment. Will make up the first part of the
            EEG filename.
        participant : str
            Participant identifier. Will make up the second part of the
            EEG filename.
        config_file : str
            The full path to the configuration file, with forward slashes
            as path separators.
        pycorder_host : string, optional
            The IP address or hostname of the computer running PyCorder.
            Defaults to ``758098-G-PC``.
        pycorder_port : int, optional
            The port on which PyCorder is listening for a connection on the
            EEG computer. This should usually not need to be changed.
            Defaults to ``6700``.
        test_mode : bool, optional
            If ``True``, the network connection to the PyCorder computer will
            not actually be initialized.
            Defaults to ``False``.
        """
        self._test_mode = test_mode

        self._pycorder_host = pycorder_host
        self._pycorder_port = pycorder_port

        self._socket = socket.socket(socket.AF_INET,
                                     socket.SOCK_STREAM)
        self._socket.settimeout(1)

        try:
            self._socket.connect((self._pycorder_host, self._pycorder_port))
        except socket.error:
            if not self._test_mode:
                msg = ('Could not connect to PyCorder at %s:%s!' %
                       (self._pycorder_host, self._pycorder_port))
                raise RuntimeError(msg)
            else:
                pass

        self._config_file = config_file
        self._exp_name = exp_name
        self._participant = participant
        self._block = 1
        self._mode = 'default'
        self._recording = False
        self._setup_pycorder()

    def __del__(self):
        self._socket.close()
        del self

    def _send(self, message):
        # Append \r\n if it's not already part of the message: PyCorder
        # uses these characters as command separators.
        if not message.endswith('\r\n'):
            message += '\r\n'

        if not self._test_mode:
            self._socket.sendall(message)
        else:
            pass

    def set_config_file(self, path):
        """
        Set the path to the configuration file. An absolute path is required.

        Parameters
        ----------
        path : string
            The path to the configuration file, e.g.,
            'C:\\Users\EEG\\Desktop\\Experiment\\config.xml'.

        """
        msg = '1%s' % path
        self._send(msg)
        time.sleep(1.2)

        msg = '4'
        self._send(msg)
        time.sleep(1.2)

        self._config_file = path

    def set_exp_name(self, name):
        """
        Set the name of the experiment or study.

        The name will make up the first part of the EEG filename.

        Parameters
        ----------
        path : string
            The name of the study or experiment, e.g., `'MyStudy2'`.


        """
        msg = '2%s' % name
        self._send(msg)
        time.sleep(1.2)

        self._exp_name = name

    def set_participant(self, participant):
        """
        Set the participant identifier.

        This identifier will make up the center part of the EEG filename.

        Parameters
        ----------
        participant : int or string
            The participant identifier, e.g., `123`.

        """
        msg = '3%s_%s' % (participant, self._block)
        self._send(msg)
        time.sleep(1.2)

        self._participant = participant

    def set_block(self, block):
        """
        Set the number of the current block.

        This number will make up the last part of the EEG filename.

        Parameters
        ----------
        block : int, or string
            The block number, e.g., `1` or `2`.

        """
        msg = '3%s_%s' % (self._participant, block)
        self._send(msg)
        time.sleep(1.2)

        self._block = block

    def _setup_pycorder(self):
        self.set_mode('default')
        self.set_config_file(self._config_file)
        self.set_exp_name(self._exp_name)
        self.set_participant(self._participant)
        self.set_block(self._block)

    def set_mode(self, mode):
        """
        Set the current mode.

        Parameters
        ----------
        mode : string
            The mode to switch to. `impedance` and `imp` will switch to
            impedance mode, while `monitoring` and `mon` will switch to
            monitoring mode. `default and `def` will exit impedance and
            monitoring mode.

        """
        if (mode == 'impedance') or (mode == 'imp'):
            self._mode = 'impedance'
            msg = 'I'
        elif (mode == 'monitor') or (mode == 'mon'):
            self._mode = 'monitor'
            msg = 'M'
        elif (mode == 'default') or (mode == 'def'):
            self._mode = 'default'
            msg = 'X'
        else:
            msg = ('`mode` must be one of: impedance, imp, monitor, mon, '
                   'def, or default.')
            raise ValueError(msg)

        self._send(msg)

    def start_recording(self):
        """
        Start recording EEG.

        """
        if self._recording:
            msg = 'Recording is still in progress!'
            raise RuntimeError(msg)

        msg = 'S'
        self._send(msg)
        self._recording = True

    def stop_recording(self):
        """
        Stop recording EEG.

        """
        if not self._recording:
            msg = 'Recording has not yet been started!'
            raise RuntimeError(msg)

        msg = 'Q'
        self._send(msg)
        self._recording = False
