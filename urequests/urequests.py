import ujson
import usocket
try:
    import ussl
    SUPPORT_SSL = True
except ImportError:
    ussl = None
    SUPPORT_SSL = False

class Response:

    def __init__(self, f):
        self.raw = f
        self.encoding = "utf-8"
        self._cached = None
        self.etag = None

    def close(self):
        if self.raw:
            self.raw.close()
            self.raw = None
        self._cached = None

    @property
    def content(self):
        if self._cached is None:
            self._cached = self.raw.read()
            self.raw.close()
            self.raw = None
        return self._cached

    @property
    def text(self):
        return str(self.content, self.encoding)

    def json(self):
        return ujson.loads(self.content)


def add_comma(iterable):
    it = iter(iterable)
    last = next(it)
    for val in it:
        yield last, ','
        last = val
    yield last, ''


def request(method, url, data=None, json=None, headers={}, stream=None, debug=False, out_file=None, in_file=None, log_format=None):
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    if proto == 'http:':
        port = 80
    elif proto == 'https:':
        port = 443
    else:
        raise OSError('Unsupported protocol: %s' % proto[:-1])
    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    ai = usocket.getaddrinfo(host, port)
    addr = ai[0][-1]
    s = usocket.socket()
    try:
        s.connect(addr)
        if proto == 'https:':
            if not SUPPORT_SSL: print('HTTPS not supported: could not find ussl')
            s = ussl.wrap_socket(s, server_hostname=host)
        if debug:
            print(b"%s /%s HTTP/1.0\r\n" % (method, path))
        s.write(b"%s /%s HTTP/1.0\r\n" % (method, path))
        if not "Host" in headers:
            if debug:
                print(b"Host: %s\r\n" % host)
            s.write(b"Host: %s\r\n" % host)
        if json is not None:
            assert data is None
            data = ujson.dumps(json)
            s.write(b'Content-Type: application/json\r\n')
        # Iterate over keys to avoid tuple alloc
        for k in headers:
            if debug:
                print('{}:{}'.format(str(k),str(headers[k])))
            s.write(str(k))
            s.write(b": ")
            s.write(str(headers[k]))
            s.write(b"\r\n")
        if data:
            if debug:
                print(b"Content-Length: {:d}\r\n".format(len(data)))
            s.write(b"Content-Length: {:d}\r\n".format(len(data)))
        elif in_file:
            s.write(b'Content-Type: application/json\r\n')
            import uos
            length = 0
            with open(in_file, mode='r') as infile:
                for line in infile:
                    to_add = len(line) + 13 # add 13 for the {"text: " "}
                    if to_add > 0:
                        to_add = to_add - 1 # minus one for the \n
                    length += to_add
                length = length + 2 - 1 # Two for the brackets and minus one for the lack of comma on the last
            if debug:
                print(b"Content-Length: {:d}\r\n".format(length))
            s.write(b"Content-Length: {:d}\r\n".format(length))
            del(uos)
        if debug:
            print(b"\r\n")
        s.write(b"\r\n")
        if data:
            if debug:
                print(data)
            s.write(data)
        # such hacks, much wow
        elif in_file and log_format:
            if debug:
                print('[')
            s.write('[')
            with open(in_file, mode='r') as infile:
                for line, comma in add_comma(infile):
                    line = line.replace('\n','')
                    json_line = '{"text": "'+line+'"}' + comma
                    if debug: print(json_line)
                    s.write(json_line)
            if debug:
                print(']')
                print('Logs Flushed')
            s.write(']')


        l = s.readline()
        protover, status, msg = l.split(None, 2)
        status = int(status)
        etag = None
        content_hmac = None
        date_line = None
        if debug: print(l)
        while True:
            l = s.readline()
            if debug:
                print(l)
            if l.startswith(b"Date:"):
                date_line = str(l[:-2:]).split(' ', 1)[1][:-1:]
            if l.startswith(b"ETag:"):
                etag = str(l).split('"')[1].rsplit('"')[0]
            if l.startswith(b"Content-HMAC:") or l.startswith(b"Content-Hmac:"):
                content_hmac = str(l).split('"')[1].rsplit('"')[0]
            if not l or l == b"\r\n":
                break

            if l.startswith(b"Transfer-Encoding:"):
                if b"chunked" in line:
                    raise ValueError("Unsupported " + l)
            elif l.startswith(b"Location:") and not 200 <= status <= 299:
                raise NotImplementedError("Redirects not yet supported")

        resp = Response(s)
        resp.status_code = status
        resp.reason = msg.rstrip()
        # This removes a RAM usage optimization but allows us to always close the socket in the finally
        if out_file:
            with open(out_file, 'wb') as file:
                buf = s.read(256)
                while buf:
                    file.write(buf)
                    buf = s.read(256)
        else:
            resp._cached = s.read()
            if debug:
                print(resp._cached)
        if date_line:
            resp.date = date_line
        if etag:
            resp.etag = etag
        if content_hmac:
            resp.content_hmac = content_hmac
        return resp
    except OSError as ex:
        print('Error handling response: {}'.format(ex))
    finally:
        s.close()


def head(url, **kw):
    return request("HEAD", url, **kw)

def get(url, **kw):
    return request("GET", url, **kw)

def post(url, **kw):
    return request("POST", url, **kw)

def put(url, **kw):
    return request("PUT", url, **kw)

def patch(url, **kw):
    return request("PATCH", url, **kw)

def delete(url, **kw):
    return request("DELETE", url, **kw)
