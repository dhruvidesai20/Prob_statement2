import random
import datetime
import uuid

_DATA_KEYS = ["a","b","c"]
class Device:
    def __init__(self, id):
        self._id = id
        self.records = []
        self.sent = []


    def obtainData(self) -> dict:
        """Returns a single new datapoint from the device.
        Identified by type `record`. `timestamp` records when the record was sent and `dev_id` is the device id.
        `data` is the data collected by the device."""
        if random.random() < 0.4:
            # Sometimes there's no new data
            return {}


        rec = {
            'type': 'record', 'timestamp': datetime.datetime.now().isoformat(), 'dev_id': self._id,
            'data': {kee: str(uuid.uuid4()) for kee in _DATA_KEYS}
        };self.sent.append(rec)
        return rec


    def probe(self) -> dict:
        """Returns a probe request to be sent to the SyncService.
        Identified by type `probe`. `from` is the index number from which the device is asking for the data."""
        if random.random() < 0.5:
            # Sometimes the device forgets to probe the SyncService
            return {}


        return {'type': 'probe', 'dev_id': self._id, 'from': len(self.records)}


    def onMessage(self, data: dict):
        """Receives updates from the server"""
        if random.random() < 0.6:
            # Sometimes devices make mistakes. Let's hope the SyncService handles such failures.
            return
       
        if data['type'] == 'update':
            _from = data['from']
            if _from > len(self.records):
                return
            self.records = self.records[:_from] + data['data']


class SyncService:
    def __init__(self):
        self.main_records= []
       
    def onMessage(self, data: dict):
        device_instance= Device(data['dev_id'])
        if data['type']== 'update':
            self.main_records.append(device_instance.records)
        elif data['type']== 'probe':
            received_data= device_instance.obtainData()
            return{'type':'update', 'data': received_data}

        """Handle messages received from devices.
        Return the desired information in the correct format (type `update`, see Device.onMessage and testSyncing to understand format intricacies) in response to a `probe`.
        No return value required on handling a `record`."""


def testSyncing():
    devices = [Device(f"dev_{i}") for i in range(10)]
    syn = SyncService()
   
    _N = int(1e6)
    for i in range(_N):
        for _dev in devices:
            syn.onMessage(_dev.obtainData())
            _dev.onMessage(syn.onMessage(_dev.probe()))


    done = False
    while not done:
        for _dev in devices: _dev.onMessage(syn.onMessage(_dev.probe()))
        num_recs = len(devices[0].records)
        done = all([len(_dev.records) == num_recs for _dev in devices])


    ver_start = [0] * len(devices)
    for i,rec in enumerate(devices[0].records):
        _dev_idx = int(rec['dev_id'].split("_")[-1])
        assertEquivalent(rec, devices[_dev_idx].sent[ver_start[_dev_idx]])
        for _dev in devices[1:]:
            assertEquivalent(rec, _dev.records[i])
        ver_start[_dev_idx] += 1
   
def assertEquivalent(d1:dict, d2:dict):
    assert d1['dev_id'] == d2['dev_id']
    assert d1['timestamp'] == d2['timestamp']
    for kee in _DATA_KEYS:
        assert d1['data'][kee] == d2['data'][kee]
