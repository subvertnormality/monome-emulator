"""Successful bodies permit reuse; rejected unread bodies close the connection."""
import http.client,json,unittest
from automation import session

class HTTPReuse(unittest.TestCase):
    def test_reuse_and_rejected_body_framing(self):
        info=session.start();connection=http.client.HTTPConnection('127.0.0.1',info['port'],timeout=5)
        auth={'Authorization':'Bearer '+info['token'],'Content-Type':'application/json'}
        try:
            connection.request('GET','/health',headers=auth)
            response=connection.getresponse();self.assertEqual(response.status,200);response.read()
            self.assertEqual(response.version,11);self.assertFalse(response.will_close)
            original=connection.sock
            connection.request('POST','/client/heartbeat',json.dumps({'client_id':'reuse'}),auth)
            response=connection.getresponse();self.assertEqual(response.status,200);response.read()
            self.assertIs(connection.sock,original)
            connection.request('GET','/snapshot',headers=auth)
            response=connection.getresponse();self.assertEqual(response.status,200);response.read()
            self.assertIs(connection.sock,original)
            for headers,expected in [({'Content-Type':'application/json'},401),
                                     (dict(auth,Origin='http://wrong-origin'),400),
                                     (dict(auth,**{'Content-Length':'999999999'}),400)]:
                connection.request('POST','/client/heartbeat','{}',headers)
                response=connection.getresponse();self.assertEqual(response.status,expected)
                self.assertTrue(response.will_close);self.assertEqual(response.getheader('Connection'),'close');response.read()
                self.assertIsNone(connection.sock)
                connection.request('GET','/health',headers=auth)
                response=connection.getresponse();self.assertEqual(response.status,200);response.read()
        finally:connection.close();session.stop(info['session_id'])

if __name__=='__main__':unittest.main()
