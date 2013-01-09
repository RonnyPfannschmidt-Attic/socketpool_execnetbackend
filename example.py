import argparse
import execnet
import socketpool.pool
import socketpool_execnetbackend
import couchdbkit

parser = argparse.ArgumentParser()
parser.add_argument('gateway')
parser.add_argument('server', default=None)

opts = parser.parse_args()

print 'making gateway'
gw = execnet.makegateway(opts.gateway)

print 'making backend'
backend = socketpool_execnetbackend.ExecnetBackend(gw)

print 'making pool'
pool = socketpool.ConnectionPool(
    socketpool_execnetbackend.connector_type(),
    backend=backend)

print 'making server'
server = couchdbkit.Server(opts.server, pool=pool)

print 'info'
print server.info()
print server.all_dbs()
