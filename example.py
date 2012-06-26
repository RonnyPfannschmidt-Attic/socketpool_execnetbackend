
import execnet
import socketpool
import couchdbkit
import socketpool_execnetbackend

gw = execnet.makegateway()

backend = socketpool_execnetbackend.ExecnetBackend(gw)
import sys
sys.modules['socketpool.backend_execnet'] = backend

server = couchdbkit.Server(backend='execnet')


print server.info()
