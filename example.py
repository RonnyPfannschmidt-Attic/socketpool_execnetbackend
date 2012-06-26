
import execnet
import socketpool.pool
import couchdbkit
import socketpool_execnetbackend

gw = execnet.makegateway()

backend = socketpool_execnetbackend.ExecnetBackend(gw)
import sys
sys.modules['socketpool.backend_execnet'] = backend


pool = socketpool.ConnectionPool(
    socketpool_execnetbackend.connector_type(),
    backend='execnet' )

server = couchdbkit.Server(pool=pool)


print server.info()
print server.all_dbs()
