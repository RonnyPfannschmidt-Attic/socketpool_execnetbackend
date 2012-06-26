

import socket
import threading

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

class ExecnetBackend(object):

    

    def __init__(self, gw):
        self.gw = gw
        import sys
        self.chan = gw.remote_exec(sys.modules[__name__])

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
        return [reverse(x) for x in results]



class RemoteSocket(object):
    def __init__(self, chan):
        self.chan = chan
        chan.reconfigure(False, False)

    def __getattr__(self, methodname):
        def standin(*k, **kw):
            self.chan.send((methodname, k, kw))
            return self.chan.receive()
        standin.__name__ = methodname
        return standin


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
            result =getattr(socket,method)(*args, **kwargs)
            chan.send(result)

    chan.setcallback(socket_data_callback, endmarker=closed)




def do_select(chan, lists, **kw):
    args = []
    for list in lists:
        args.append([sockets[x] for x in list])
    results = select(*args, **kw)
    send = []
    for res in results:
        sent.append([channels[s] for s in res])
    chan.send(send)




if __name__ == '__channelexec__':
    sockets = {}
    channels = {}

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
