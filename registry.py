import asyncio
import logging
from typing import List, Dict

import aiohttp

from database.database import Database


class Registry:
    MIN_DELEGATION = 1000
    def __init__(self, chain_name: str, db: Database):
        self.rest_arr = None
        if chain_name:
            self.chain = chain_name
            self.db = db

    async def get_chain_registry(self) -> List:
        """Get chains list from cosmos chains registry"""
        res = []
        async with aiohttp.ClientSession() as session:
            registry_url = 'https://cosmos-chain.directory/chains'
            async with session.get(registry_url) as resp:
                if resp.status == 200:
                    chains = await resp.json()
                    for chain in chains['chains']:
                        res.append(await self.get_chain_info(chain_name=chain))
                    return res
                else:
                    return []

    async def get_chain_info(self, chain_name: str) -> Dict:
        """Get chain info by chain_name from cosmos chains registry"""
        async with aiohttp.ClientSession() as session:
            chain_url = f'https://cosmos-chain.directory/chains/{chain_name}'
            async with session.get(chain_url) as resp:
                if resp.status == 200:
                    chain = await resp.json()
                    if 'apis' not in chain:
                        return {"rpcs": [], "bech32_prefix": None}
                    rpcs = chain['apis']['rest']
                    bech32_prefix = chain['bech32_prefix']
                    logging.info(f'fetched new chain: {bech32_prefix}')
                    return {"rpcs": rpcs, "bech32_prefix": bech32_prefix, "chain_name": chain['chain_name']}
                else:
                    return {"rpcs": [], "bech32_prefix": None, "chain_name": None}

    async def check_node(self, rest_arr):
        """checking rest node status"""
        for i in rest_arr:
            url = f"{i['rest_url']}/node_info"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return i
        return rest_arr[0]

    async def check_wallet_is_correct(self, wallet: str) -> bool:
        """check if wallet exist"""
        async with aiohttp.ClientSession() as session:
            self.rest_arr = await self.db.get_rest(self.chain)
            work_rest = await self.check_node(self.rest_arr)  # get alive rest url
            url = f"{work_rest['rest_url']}/cosmos/bank/v1beta1/balances/{wallet}"

            async with session.get(url) as resp:
                if resp.status == 200:
                    logging.info(resp.status)
                    balances = await resp.json()
                    if balances['balances']:
                        logging.info(f"fetched balances for wallet {wallet}: {balances['balances']}")
                    return True
                else:
                    logging.error(resp)
                    return False

    async def check_delegated_balance(self, wallet: str, validator: str) -> bool:
        """check delegated balance by validator and wallet. If delegated balance > 10k return true"""
        async with aiohttp.ClientSession() as session:
            self.rest_arr = await self.db.get_rest(self.chain)
            work_rest = await self.check_node(self.rest_arr)  # get alive rest url
            url = f"{work_rest['rest_url']}/cosmos/staking/v1beta1/validators/{validator}/delegations/{wallet}"

            async with session.get(url) as resp:
                if resp.status == 200:
                    logging.info(resp.status)
                    delegation = await resp.json()
                    logging.info(delegation)
                    if delegation['delegation_response']['delegation']:
                        logging.info(f"fetched delegation for wallet {wallet}: {delegation['delegation_response']['delegation']['shares']}") 
                        tmp_min_delegation = self.MIN_DELEGATION
                        if wallet[0:3] in ('fet', 'sif'):
                            tmp_min_delegation = 10000
                        return float(delegation['delegation_response']['delegation']['shares']) >= tmp_min_delegation
                else:
                    logging.error(resp)
                    return False

    async def get_validators_by_wallet(self, wallet: str) -> List[str]:
        async with aiohttp.ClientSession() as session:
            self.rest_arr = await self.db.get_rest(self.chain)
            work_rest = await self.check_node(self.rest_arr)  # get alive rest url
            url = f"{work_rest['rest_url']}/cosmos/distribution/v1beta1/delegators/{wallet}/validators?pagination.limit=100"

            async with session.get(url) as resp:
                if resp.status == 200:
                    logging.info(resp.status)
                    delegator = await resp.json()
                    logging.info(f"fetched validators for wallet {wallet}: {len(delegator['validators'])}")
                    return delegator['validators']
                else:
                    logging.error(resp)
                    return []

    async def get_chain_validators(self) -> List:
        async with aiohttp.ClientSession() as session:
            self.rest_arr = await self.db.get_rest(self.chain)
            work_rest = await self.check_node(self.rest_arr)  # get alive rest url
            url = f"{work_rest['rest_url']}/cosmos/staking/v1beta1/validators?pagination.limit=600"
            async with session.get(url) as resp:
                if resp.status == 200:
                    chain_validators = await resp.json()
                    return chain_validators['validators']
                else:
                    return []
