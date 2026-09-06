import unittest
from devices.midi import configuration,Decoder,Capture
from automation.protocol import ContractError

class MidiContracts(unittest.TestCase):
    def test_configuration_and_channel_boundaries(self):
        for value in ({}, {'ports':[]}, {'ports':['x','x']}, {'ports':['bad\nname']}, {'ports':['none']}, {'ports':['x'],'capture_limit':False}):
            with self.assertRaises(ContractError): configuration(value)
        for channel in range(16):
            value=Decoder().feed([144+channel,60,127,60,0])
            self.assertEqual(value,[dict(type='note_on',channel=channel+1,data=[60,127]),dict(type='note_off',channel=channel+1,data=[60,0])])
    def test_interleaved_realtime_running_status_and_sysex(self):
        decoder=Decoder()
        self.assertEqual(decoder.feed([144,60,248,100]),[dict(type='clock'),dict(type='note_on',channel=1,data=[60,100])])
        self.assertEqual(decoder.feed([61,0]),[dict(type='note_off',channel=1,data=[61,0])])
        self.assertEqual(decoder.feed([240,1,248,2,247]),[dict(type='clock'),dict(type='sysex',bytes=[240,1,2,247])])
        with self.assertRaises(ContractError): decoder.feed([1])
    def test_capture_drop_overflow_order_and_notes(self):
        capture=Capture(['a','b'],4)
        capture.accept(1,2,100,[145,60,127]);capture.accept(2,1,100,[145,60,100])
        capture.accept(3,2,101,[145,60,0])
        self.assertEqual(capture.state()['outstanding'],[dict(port=1,channel=2,note=60,count=1)])
        with self.assertRaises(ContractError) as error: capture.accept(5,1,102,[248])
        self.assertEqual(error.exception.code,'midi_drop')
        with self.assertRaises(ContractError): capture.accept(4,1,99,[248])
        capture.accept(4,1,102,[177,123,0]);self.assertEqual(capture.state()['outstanding'],[])
        with self.assertRaises(ContractError) as error: capture.accept(5,1,103,[248])
        self.assertEqual(error.exception.code,'midi_overflow')
