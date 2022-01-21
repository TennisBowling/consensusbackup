import consensusbackup
from sanic import Sanic, response
from sanic.request import Request
from platform import python_version, system, release, machine

app = Sanic('router')
    
router = consensusbackup.NodeRouter([''])

@app.before_server_start
async def before_start(app, loop):
    await router.setup()
    app.add_task(router.repeat_check(), name='repeat_check')

@app.before_server_stop
async def after_stop(app, loop):
    await router.stop()
    await app.cancel_task('repeat_check')
    
@app.route('/<path:path>', methods=['GET', 'POST'])
async def route(request: Request, path: str):
    data, status = await router.route(request.method, request.raw_url.decode(), request.json)
    return response.text(data, status=status)

@app.route('/eth/v1/events', methods=['GET'], stream=True)
async def eventsub(request: Request):
    response = await request.respond(content_type='text/event-stream')
    await router.stream(request.raw_url.decode(), response, request.json)

@app.route('/consensusbackup/version', methods=['GET'])
async def ver(request: Request):
    return response.text(f'consensusbackup-{consensusbackup.__version__}/{system() + release()}-{machine()}/python{python_version()}')

@app.route('/consensusbackup/status', methods=['GET'])
async def status(request: Request):
    #await router.recheck()
    ok = 200 if router.alive_count > 0 else 503
    return response.json({'status': 200 if router.alive_count > 0 else 503, 'alive': router.alive_count, 'dead': router.dead_count}, status=ok)

@router.listener('node_offline')
async def node_offline(url: str):
    print(f'Node {url} is offline')

@router.listener('all_nodes_offline')
async def all_nodes_offline():
    print('All nodes are offline!')

@router.listener('node_online')
async def node_online(url: str):
    print(f'Node {url} is online')

@router.listener('node_router_online')
async def node_router_online():
    print('Node router online')

app.run('0.0.0.0', port=8000, access_log=True)
