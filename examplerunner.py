import consensusbackup
from sanic import Sanic, response
from sanic.request import Request
from platform import python_version, system, release, machine

app = Sanic('router')
    
router = consensusbackup.NodeRouter(['https://23sK9Q1vqZps6LThtNu1k8dWvx5:5103cd928c51b464fa289af3ef3d395e@eth2-beacon-mainnet.infura.io', 'http://unstable.mainnet.beacon-api.nimbus.team', 'http://testing.mainnet.beacon-api.nimbus.team'])
perms = [] # a list of allowed tokens to access the API

@app.before_server_start
async def before_start(app: Sanic, loop):
    await router.setup()
    app.add_task(router.repeat_check())

@app.before_server_stop
async def after_stop(app: Sanic, loop):
    await router.stop()
    await app.cancel_task('repeat_check')
    
@app.route('/<path:path>', methods=['GET', 'POST'])
async def route(request: Request, path: str):
    if request.headers.pop('Authorization') not in perms:
        return response.json({'error': 'unauthorized. please check the Authorization header.'}, status=401)
    data, status = await router.route(request.method, request.raw_url.decode(), request.json)
    return response.text(data, status=status)

@app.route('/eth/v1/events', methods=['GET'], stream=True)
async def eventsub(request: Request):
    if request.headers.pop('Authorization') not in perms:
        return response.json({'error': 'unauthorized. please check the authorization header.'}, status=401)
    response = await request.respond(content_type='text/event-stream')
    await router.stream(request.raw_url.decode(), response, request.json)

@app.route('/consensusbackup/version', methods=['GET'])
async def ver(request: Request):
    return response.text(f'consensusbackup-{consensusbackup.__version__}/{system() + release()}-{machine()}/python{python_version()}')

@app.route('/consensusbackup/status', methods=['GET'])
async def status(request: Request):
    #await router.recheck()
    ok = 200 if router.alive_count > 0 else 503
    return response.json({'status': ok, 'alive': router.alive_count, 'dead': router.dead_count}, status=ok)

@app.route('/consensusbackup/setpermissions', methods=['POST'])
async def setpermissions(request: Request):
    if not request.headers.get('permissionskey') == 'I love tennis':
        return response.json({'error': 'unauthorized'}, status=401)
    perms.append(request.json['permissions'])
    return response.json({'permissions': perms})

@app.route('/consensusbackup/removepermissions', methods=['POST'])
async def removepermissions(request: Request):
    if not request.headers.get('permissionskey') == 'I love tennis':
        return response.json({'error': 'unauthorized'}, status=401)
    try:
        perms.remove(request.json['permissions'])
    except ValueError:
        pass
    return response.json({'permissions': perms})

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

app.run('127.0.0.1', port=8000, access_log=False)
