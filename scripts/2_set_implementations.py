from brownie import Contract, chain, accounts, AllowlistImplementationYearnVaults, ZERO_ADDRESS
import json

def main():
    # Setup
    protocol_configuration = json.load(open('configuration/protocol.json', 'r'))
    allowlist_addresses = json.load(open('configuration/allowlist.json', 'r'))
    origin_name = protocol_configuration["originName"]
    allowlist_addresses = allowlist_addresses["networkVariables"][str(chain.id)]
    allowlist_addresses = protocol_configuration["networkVariables"][str(chain.id)]
    allowlist_factory_address = allowlist_addresses["allowlist_factory_address"]
    allowlist_factory = Contract(allowlist_factory_address)
    allowlist_address = allowlist_factory.allowlistAddressByOriginName(origin_name)
    allowlist = Contract(allowlist_address)
    if (allowlist_address == ZERO_ADDRESS):
        print("Protocol has not yet registered.")
        print("Please complete step 1, or begin the registration process at:", allowlist_factory_address)
        return
    owner_address = allowlist_factory.protocolOwnerAddressByOriginName(origin_name)
    owner = accounts.at(owner_address, force=True)
    
    # Implementation
    print("Deploying implementation logic...")
    addresses_provider_address = allowlist_addresses["addresses_provider_address"]
    implementation = AllowlistImplementationYearnVaults.deploy(addresses_provider_address, {"from": owner})
    
    # Conditions
    print("Adding conditions...")
    conditions = [(
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ],
        implementation
    )]
    conditions_length_before = allowlist.conditionsLength()
    allowlist.addConditions(conditions, {"from": owner})
    
    # Testing
    conditions_length_after = allowlist.conditionsLength()
    if conditions_length_after > conditions_length_before:
        print("Adding conditions was successful")
    else:
        print("Error adding conditions")
