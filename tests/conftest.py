import pytest
from brownie import Contract, ZERO_ADDRESS, accounts, chain
import json

##############################################################
# Setup and configuration
##############################################################

@pytest.fixture
def conditions():
    return json.load(open('configuration/chains/' + str(chain.id) + '/conditions.json', 'r'))

@pytest.fixture
def allowlist_configuration():
    return json.load(open('configuration/chains/' + str(chain.id) + '/allowlist.json', 'r'))

@pytest.fixture
def allowlist_addresses():
    return json.load(open('configuration/chains/' + str(chain.id) + '/addresses.json', 'r'))

@pytest.fixture
def protocol_configuration():
    return json.load(open('configuration/protocol.json', 'r'))

@pytest.fixture
def origin_name(protocol_configuration):
    return protocol_configuration["originName"]

@pytest.fixture
def allowlist_registry(allowlist_configuration):
    allowlist_registry_address = allowlist_configuration["allowlist_registry_address"]
    return Contract(allowlist_registry_address)

@pytest.fixture
def allowlist_factory(allowlist_registry):
    allowlist_factory_address = allowlist_registry.factoryAddress()
    return Contract(allowlist_factory_address)

@pytest.fixture
def owner(allowlist_registry, origin_name):
    owner_address = allowlist_registry.protocolOwnerAddressByOriginName(origin_name)
    return accounts.at(owner_address, force=True)

@pytest.fixture
def address_provider(allowlist_addresses):
    return Contract(allowlist_addresses["addresses_provider_address"])
    
##############################################################
#  Protocol registration and condition management
##############################################################
@pytest.fixture(autouse=True)
def allowlist(allowlist_registry, owner, origin_name):
    # Register protocol
    allowlist_address = allowlist_registry.allowlistAddressByOriginName(origin_name)
    registration_started = allowlist_address != ZERO_ADDRESS
    if  registration_started == False:
        allowlist_registry.register(origin_name, {"from": owner})
        
    # Make sure a new allowlist was generated
    allowlist_address = allowlist_registry.allowlistAddressByOriginName(origin_name)
    assert allowlist_address != ZERO_ADDRESS
    allowlist = Contract(allowlist_address)
    assert allowlist.name() == origin_name
    
    # Return allowlist
    return Contract(allowlist_address)

@pytest.fixture
def condition_by_id(conditions):
    def make_condition_by_id(id):
        for condition in conditions:
            if condition['id'] == id:
                return (
                    condition['id'],
                    condition['implementationId'],
                    condition['methodName'],
                    condition['paramTypes'],
                    condition['requirements'],
                )
    return make_condition_by_id
