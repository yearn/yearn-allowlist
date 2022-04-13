from brownie import Contract, chain, accounts, ZERO_ADDRESS, AllowlistImplementationYearnVaults, AllowlistImplementationIronBank
import json

def format_conditions(conditions):
    formatted_conditions = []
    for condition in conditions:
        current_condition = (
            condition['id'],
            condition['implementationId'],
            condition['methodName'],
            condition['paramTypes'],
            condition['requirements'],
        )
        formatted_conditions.append(current_condition)
    return formatted_conditions

def deploy_implementation_yearn_vaults(args):
    addresses_provider = args[0]
    factory = args[1]
    owner = args[2]
    return AllowlistImplementationYearnVaults.deploy(addresses_provider, factory, {"from": owner})

def deploy_implementation_iron_bank(args):
    addresses_provider = args[0]
    owner = args[1]
    return AllowlistImplementationIronBank.deploy(addresses_provider, {"from": owner})
    
def main():
    ##########################################
    # Setup
    ##########################################
    protocol_configuration = json.load(open('configuration/protocol.json', 'r'))
    allowlist_addresses = json.load(open('configuration/chains/' + str(chain.id) + '/addresses.json', 'r'))
    allowlist_configuration = json.load(open('configuration/chains/' + str(chain.id) + '/allowlist.json', 'r'))
    conditions_configuration = json.load(open('configuration/chains/' + str(chain.id) + '/conditions.json', 'r'))
    
    print()
    print("Searching for allowlist registry...")
    key = "originName"
    if key in protocol_configuration:
        origin_name = protocol_configuration["originName"]
        print("Found protocol origin:   ", origin_name)
    else:
        print("Error: Protocol origin not set (check configuration/protocol.json)")
        return
    origin_name = protocol_configuration["originName"]
    
    key = "allowlist_registry_address"
    if key in allowlist_configuration:
        allowlist_registry = Contract(allowlist_configuration[key])
        print("Found allowlist registry:", allowlist_registry)
    else:
        print("Error: Allowlist registry does not exist (check configuration/chains/<id>/allowlist.json)")
        return
    allowlist_factory = Contract(allowlist_registry.factoryAddress())

    if allowlist_factory != ZERO_ADDRESS:
        print("Found allowlist factory: ", allowlist_factory)
    else:
        print("Error: Allowlist factory does not exist on registry:", allowlist_registry)
        return

    allowlist_address = allowlist_registry.allowlistAddressByOriginName(origin_name)
    if allowlist_address != ZERO_ADDRESS:
        print("Found allowlist:         ", allowlist_address)
    owner_address = allowlist_registry.protocolOwnerAddressByOriginName(origin_name)
    owner = accounts.at(owner_address, force=True)
    print()
    
    ##########################################
    # Registration
    ##########################################
    print("Starting protocol registration...")
    if (allowlist_address != ZERO_ADDRESS):
        print("Skipping registration:    Protocol is already registered")
    else:
        # Registration
        allowlist_registry.registerProtocol(origin_name, {"from": owner})
    
        # Test registration
        allowlist_address = allowlist_registry.allowlistAddressByOriginName(origin_name)
        if (allowlist_address != ZERO_ADDRESS):
            print("Protocol successfully registered.")
            print("To continue, add implementations and conditions to your allowlist:", allowlist_address)
        else:
            print("Error: protocol registration was unsuccessful")
            return
    allowlist = Contract(allowlist_address)
    assert allowlist != ZERO_ADDRESS
    print()
            
    ##########################################
    # Implementations
    ##########################################
    # Gather arguments
    key = "addresses_provider_address"
    if key in allowlist_addresses:
        addresses_provider = Contract(allowlist_addresses[key])    
    else:
        "Error: cannot find addresses provider"
        return
        
    # Set implementations
    implementations = [
        {
            "id": "IMPLEMENTATION_YEARN_VAULTS",
            "deployment_method": deploy_implementation_yearn_vaults,
            "arguments": [addresses_provider, allowlist_factory, owner],
            "override": False
        },
        {
            "id": "IMPLEMENTATION_IRON_BANK",
            "deployment_method": deploy_implementation_iron_bank,
            "arguments": [addresses_provider, allowlist_factory, owner],
            "override": False
        }
    ]

    # Deploy implementations
    print("Deploying implementations...")
    for implementation in implementations:
        implementation_id = implementation['id']
        implementation_deployment_method = implementation['deployment_method']
        implementation_arguments = implementation['arguments']
        
        implementation_address = allowlist.implementationById(implementation_id)
        if implementation_address == ZERO_ADDRESS:
            print("Deploying:               ", implementation_id, "...")
            deployment_address = implementation_deployment_method(implementation_arguments)
            print("Setting implementation:  ", implementation_id, deployment_address)
            allowlist.setImplementation(implementation_id, deployment_address, {"from": owner})
            assert allowlist.implementationById(implementation_id) != ZERO_ADDRESS
            print()
        else:
            print("Deployment exists (skipping):", implementation_id, implementation_address)
            print()
        

    ##########################################
    # Conditions
    ##########################################
    # Set conditions
    print("Adding conditions...")
    conditions = format_conditions(conditions_configuration)
    allowlist.addConditions(conditions, {"from": owner})
    
    # Validate results
    print("Validating results...")
    conditions_json = allowlist.conditionsJson()
    assert len(conditions_json) > 0
    # print(conditions_json)
    
    print("Success!!")
    