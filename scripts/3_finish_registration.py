from brownie import Contract, chain, accounts, ZERO_ADDRESS
import json

def main():
    # Setup
    protocol_configuration = json.load(open('configuration/protocol.json', 'r'))
    allowlist_configuration = json.load(open('configuration/allowlist.json', 'r'))
    origin_name = protocol_configuration["originName"]
    allowlist_variables = allowlist_configuration["networkVariables"][str(chain.id)]
    allowlist_factory_address = allowlist_variables["allowlist_factory_address"]
    allowlist_factory = Contract(allowlist_factory_address)
    print("Finishing protocol registration...")
    registered = allowlist_factory.registeredProtocol(origin_name) == True
    if registered:
        print("Protocol is already registered.")
        return
    owner_address = allowlist_factory.protocolOwnerAddressByOriginName(origin_name)
    owner = accounts.at(owner_address, force=True)
    
    # Registration
    allowlist_factory.finishProtocolRegistration(origin_name, {"from": owner})
    
    # Testing
    registered = allowlist_factory.registeredProtocol(origin_name) == True
    if registered:
        print("Protocol was successfully registered.")
    else:
        print("There was a problem during registration.")
