import aiohttp
from typing import *
from asyncio import sleep, shield
from . import logger


class ServerOffline(Exception):
    pass

class NodeInstance:
    def __init__(self, url: str):
        self.url: str = url
        self.session = aiohttp.ClientSession(headers={'Accept': 'application/json'})
        self.status: bool = False
        self.dispatch = logger.dispatch
    
    async def set_online(self):
        if self.status:
            return
        self.status = True
        await self.dispatch('node_online', self.url)
    
    async def set_offline(self):
        if not self.status:
            return
        self.status = False
        await self.dispatch('node_offline', self.url)

    async def check_alive(self) -> bool:
        try:
            async with self.session.get(f'{self.url}/eth/v1/node/health') as resp:
                if resp.status == 200:
                    await self.set_online()
                    return True
        except:
            await self.set_offline()
            return False
    
    async def do_request(self, method: str, path: str, data: Dict[str, Any]=None) -> Tuple[Optional[Dict[str, Any]], int]:
        try:
            async with self.session.request(method, f'{self.url}{path}', json=data) as resp:
                return ((await resp.json()), resp.status)
        except:
            await self.set_offline()
            return ServerOffline('Server is offline')

    async def stop(self):
        await self.session.close()

class NodeRouter:
    def __init__(self, urls: List[str]):
        if not urls:
            raise ValueError('No nodes provided')
        self.urls = urls
        self.dispatch = logger.dispatch
        self.listener = logger.listener
    
    async def recheck(self) -> None:
        for node in self.nodes:
            await node.check_alive()
    
    async def repeat_check(self) -> None:
        while True:
            await self.recheck()
            await sleep(600)

    async def setup(self) -> None:
        self.nodes: List[NodeInstance] = [NodeInstance(url) for url in self.urls]
        await self.recheck()
        await self.dispatch('node_router_online')
    
    async def get_alive_node(self) -> Optional[NodeInstance]:
        for node in self.nodes:
            if node.status:
                if await node.check_alive():
                    return node
        return None
    
    async def do_request(self, method: str, path: str, request: Dict[str, Any]=None) -> Tuple[Optional[Dict[str, Any]], int]:
        node = await self.get_alive_node()
        try:
            return await node.do_request(method, path, request)
        except ServerOffline:
            return None
        except AttributeError:
            return None # you're out of nodes
    
    async def route(self, method: str, path: str, request: Dict[str, Any]=None) -> Tuple[Dict[str, Any], int]:
        data, status = await self.do_request(method, path, request)
        counter = 0
        while not data:
            data = await self.do_request(method, path, request)
            counter += 1
            if counter > len(self.nodes):
                await self.dispatch('all_nodes_offline')
                return ({'error': 'All nodes are offline'}, 503)
        return (data, status)
            
    async def stop(self) -> None:
        for node in self.nodes:
            await node.stop()