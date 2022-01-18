import consensusbackup
from sanic import Sanic, response
from sanic.request import Request

app = Sanic('router')
    
router = consensusbackup.NodeRouter(['http://127.0.0.1:5052', 'https://1pe7yRM9cjd3PEyYQQf0TItnBR7:0fb942a04ba74cf7c0a9bc1b8c2df168@eth2-beacon-mainnet.infura.io', 'http://testing.mainnet.beacon-api.nimbus.team'])

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
    try:
        data, status = await router.route(request.method, request.raw_url.decode(), request.json)
    except:
        return response.json({'error': 'Server returned unexpected reply'}, status=503)
    return response.json(data, status=status)

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