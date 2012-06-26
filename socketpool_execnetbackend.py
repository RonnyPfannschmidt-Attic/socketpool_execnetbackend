import select
import socket
import threading
DEBUG=0


def socketmap(*args):
    """
    this will get our sockets and pass them in,
    we sume identity to hold true in all cases
    """
    result = []
    mapping = {}
    for listing in args:
        arglist = []
        for item in listing:
            arglist.append(item.chan)
            mapping[item.chan] = item
        result.append(arglist)
    return result, mapping.get




def connector_type():
    import restkit.conn
    class Conn(restkit.conn.Connection):
        def is_connected(self):
            return self._s.is_connected()
    return Conn


class ExecnetBackend(object):

    def __init__(self, gw):
        self.gw = gw
        import sys
        self.chan = gw.remote_exec(sys.modules[__name__])
        self.debug_chan = gw.newchannel()
        self.chan.send(self.debug_chan)
        self.debug_chan.setcallback(do_debug)
        import socketpool.backend_thread as t
        self.t = t

    def __getattr__(self, name):
        return getattr(self.t, name)

    def Socket(self, *k, **kw):
        self.chan.send(('new', k, kw))
        return RemoteSocket(self.chan.receive())

    def Select(self, r, w, x, **kw):
        args, reverse = socketmap(r, w, x)
        self.chan.send(('select', args, kw))
        wait = self.chan.receive()
        results = wait.receive()
        returns = []
        for res in results:
            returns.append([reverse(x) for x in res])
        return returns



class RemoteSocket(object):
    def __init__(self, chan):
        self.chan = chan
        chan.reconfigure(False, False)

    def __getattr__(self, methodname):
        def standin(*k, **kw):
            debug('call', methodname, k, kw)
            self.chan.send((methodname, k, kw))
            return self.chan.receive()
        standin.__name__ = methodname
        return standin

    def recv_into(self, buffer):
        data = self.recv(len(buffer))
        buffer[:len(data)] = data
        debug('recv_into', data)
        return len(data)


closed = object()

def remote_socket_control(chan):
    def socket_data_callback(args):
        socket = sockets[chan]
        if args is closed:
            socket.close()
            del sockets[chan]
            del channels[socket]
        else:
            method, args, kwargs = args
            chan.gateway._trace("socket call", socket, method, args, kwargs)
            if method == 'is_connected':
                try:
                    r, _, _ = select.select([socket], [], [], 0)
                except:
                    result = False
                else:
                    result = not r
            else:
                result =getattr(socket,method)(*args, **kwargs)
            chan.send(result)

    chan.setcallback(socket_data_callback, endmarker=closed)




def do_select(chan, lists, **kw):
    debug("select", chan, lists, kw)
    args = []
    try:
        for list in lists:
            args.append([sockets[x] for x in list])
        if 'timeout' in kw:
            args.append(kw.get('timeout'))
        else:
            args.append(.5)
        results = select.select(*args)
    except Exception as e:
        debug(str(e))
        #XXX: error
        chan.send(([],[],[]))
    else:
        debug('result', results)
        send = []
        for res in results:
            send.append([channels[s] for s in res])
        chan.send(send)



def do_debug(args):
    if DEBUG:
        args = [str(x) for x in args]
        print ' '.join(args)

def debug(*k):
    do_debug(k)

if __name__ == '__channelexec__':
    sockets = {}
    channels = {}
    debug_chan = channel.receive()
    def debug(*k):
        debug_chan.send(k)
    for command, args, kw in channel:
        chan = channel.gateway.newchannel()
        if command == 'new':
            s = socket.socket(*args, **kw)
            sockets[chan] = s
            channels[s] = chan
            remote_socket_control(chan)
        elif command == 'select':
            thread = threading.Thread(target=do_select, args=(chan, args), kwargs=kw)
            thread.start()
        channel.send(chan)
