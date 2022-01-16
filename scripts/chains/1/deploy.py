from brownie import Contract, chain, accounts, ZERO_ADDRESS
import json

def main():
    # Setup
    protocol_configuration = json.load(open('configuration/protocol.json', 'r'))
    allowlist_addresses = json.load(open('configuration/allowlist.json', 'r'))
    origin_name = protocol_configuration["originName"]
    allowlist_addresses = allowlist_addresses["networkVariables"][str(chain.id)]
    allowlist_factory_address = allowlist_addresses["allowlist_factory_address"]
    allowlist_factory = Contract(allowlist_factory_address)
    allowlist_address = allowlist_factory.allowlistAddressByOriginName(origin_name)
    print("Starting protocol registration...")
    if (allowlist_address != ZERO_ADDRESS):
        print("Protocol has already started registration.")
        print("Allowlist:", allowlist_address)
        return
    owner_address = allowlist_factory.protocolOwnerAddressByOriginName(origin_name)
    owner = accounts.at(owner_address, force=True)
    
    # Registration
    allowlist_factory.startProtocolRegistration(origin_name, {"from": owner})
    
    # Testing
    allowlist_address = allowlist_factory.allowlistAddressByOriginName(origin_name)
    if (allowlist_address != ZERO_ADDRESS):
        print("Protocol registration successfully started.")
        print("To continue, add conditions to your allowlist:", allowlist_address)
    else:
        print("Protocol registration was unsuccessful")