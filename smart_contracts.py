#!/usr/bin/env python3

import json
import os

import matplotlib.pyplot as plt
import requests
from dune_client.client import DuneClient
from dune_client.query import QueryBase
from dune_client.types import QueryParameter
from web3 import Web3

# trying to read smart contracts using web3.py and exploring a few APIs (DUNE, Etherscan)
infura_url = "https://mainnet.infura.io/v3/" + os.getenv("INFURA_API_KEY")
dune_url = "https://api.dune.com"
etherscan_url = "https://api.etherscan.io/api"
my_abi_query_id = 4852729  # query id from Dune
eb_genesis_contract_address = '0x8754f54074400ce745a7ceddc928fb1b7e985ed6'

# Get EulerBeats Genesis ABI from DUNE
dune = DuneClient(
    api_key=os.getenv("DUNE_API_KEY"),
    base_url=dune_url,
    request_timeout=300
)

query = QueryBase(
    name="GetABI",
    query_id=my_abi_query_id,
    params=[
        QueryParameter.text_type(name="contract_address", value=eb_genesis_contract_address)
    ],
)
results_df = dune.run_query_dataframe(query)
abi = json.loads(results_df.abi[0].replace('} {', '},{'))

# to get the most recent query results without using execution credits
# results = dune.get_latest_result(my_abi_query_id, max_age_hours=8)

# get the ABI directly from etherscan
r = requests.get(etherscan_url
                 + '?module=contract&action=getabi&address='
                 + eb_genesis_contract_address
                 + '&apikey='
                 + os.getenv('ETHERSCAN_API_KEY'))
# abi = r.json()['result']

# Read Euler Beats Genesis contract (ERC1155)
web3 = Web3(Web3.HTTPProvider(infura_url))

contract = web3.eth.contract(address=Web3.to_checksum_address(eb_genesis_contract_address), abi=abi)
# https://etherscan.io/address/0x8754f54074400ce745a7ceddc928fb1b7e985ed6#code

# list all contract functions
contract_functions = contract.all_functions()
print(len(contract_functions))
for function in contract_functions:
    print(function)

# EB Original mint price
mint_prince_wei = contract.functions.mintPrice().call()
mint_price_eth = web3.from_wei(mint_prince_wei, "ether")
print(mint_price_eth)

# get current supply of prints, print price and burn price for a given Original
seed = 21575894274  # LP01 seed: https://opensea.io/assets/ethereum/0x8754f54074400ce745a7ceddc928fb1b7e985ed6/21575894274
print_id = contract.functions.getPrintTokenIdFromSeed(seed).call()
# results should match https://eulerbeats.com/genesis/18052613891
current_supply = contract.functions.totalSupply(print_id).call() + 1
print(current_supply)
print_price = web3.from_wei(contract.functions.getPrintPrice(current_supply + 1).call(), "ether")
print(print_price)
burn_price = web3.from_wei(contract.functions.getBurnPrice(current_supply).call(), "ether")
print(burn_price)

# print price evolution
n_prints = 120
print_prices = [web3.from_wei(contract.functions.getPrintPrice(i).call(), "ether") for i in range(1, n_prints + 1)]

plt.scatter(range(1, n_prints + 1), print_prices, alpha=0.5)
plt.show(block=True)
