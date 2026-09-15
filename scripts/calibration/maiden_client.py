"""Minimal Maiden REPL client (nanomsg BUS over WebSocket), no application code."""
import ctypes, hashlib, time

AF_SP, NN_BUS, NN_SOL_SOCKET, NN_SNDTIMEO, NN_RCVTIMEO = 1, 112, 0, 4, 5


class Maiden:
    def __init__(self, url, timeout_ms=60000, library='libnanomsg.so.5'):
        nn = ctypes.CDLL(library)
        nn.nn_socket.argtypes = [ctypes.c_int, ctypes.c_int]
        nn.nn_connect.argtypes = [ctypes.c_int, ctypes.c_char_p]
        nn.nn_setsockopt.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
        nn.nn_send.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
        nn.nn_recv.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
        nn.nn_close.argtypes = [ctypes.c_int]
        self.nn, self.fd = nn, nn.nn_socket(AF_SP, NN_BUS)
        if self.fd < 0:
            raise RuntimeError('nn_socket failed')
        value = ctypes.c_int(timeout_ms)
        for option in (NN_SNDTIMEO, NN_RCVTIMEO):
            if nn.nn_setsockopt(self.fd, NN_SOL_SOCKET, option, ctypes.byref(value), ctypes.sizeof(value)) < 0:
                raise RuntimeError('nn_setsockopt failed')
        if nn.nn_connect(self.fd, url.encode()) < 0:
            raise RuntimeError('nn_connect failed')
        time.sleep(0.25)

    def eval(self, code, allow_lua_error=False):
        """Run Lua and return all output up to a unique completion marker."""
        marker = '__CAL_' + hashlib.sha256((code + str(time.monotonic_ns())).encode()).hexdigest()[:16] + '__'
        payload = (code.rstrip() + "; print('" + marker + "')\n").encode() + b'\0'
        buffer = ctypes.create_string_buffer(payload)
        if self.nn.nn_send(self.fd, buffer, len(payload), 0) != len(payload):
            raise RuntimeError('nn_send failed')
        output = []
        while True:
            received = ctypes.create_string_buffer(65536)
            size = self.nn.nn_recv(self.fd, received, len(received), 0)
            if size < 0:
                raise TimeoutError('Maiden marker not observed: ' + ''.join(output)[-2000:])
            chunk = received.raw[:size].decode(errors='replace')
            output.append(chunk)
            if 'stack traceback:' in chunk and not allow_lua_error:
                raise RuntimeError('Lua error: ' + ''.join(output)[-2000:])
            if marker in chunk:
                return ''.join(output)

    def close(self):
        if self.fd is not None:
            self.nn.nn_close(self.fd)
            self.fd = None
