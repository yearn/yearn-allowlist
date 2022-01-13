import pytest
from brownie import Contract, ZERO_ADDRESS, accounts, chain
import json

##############################################################
# Setup and configuration
##############################################################
@pytest.fixture
def allowlist_configuration():
    return json.load(open('configuration/allowlist.json', 'r'))

@pytest.fixture
def protocol_configuration():
    return json.load(open('configuration/protocol.json', 'r'))

@pytest.fixture
def origin_name(protocol_configuration):
    return protocol_configuration["originName"]

@pytest.fixture
def allowlist_factory(allowlist_variables):
    allowlist_factory_address = allowlist_variables["allowlist_factory_address"]
    return Contract(allowlist_factory_address)

@pytest.fixture
def owner(allowlist_factory, origin_name):
    owner_address = allowlist_factory.protocolOwnerAddressByOriginName(origin_name)
    return accounts.at(owner_address, force=True)

@pytest.fixture
def address_provider(network_variables):
    return Contract(network_variables["address_provider_address"])
    
@pytest.fixture
def network_variables(protocol_configuration):
    return protocol_configuration["networkVariables"][str(chain.id)]

@pytest.fixture
def allowlist_variables(allowlist_configuration):
    return allowlist_configuration["networkVariables"][str(chain.id)]

##############################################################
#  Protocol registration and condition management
##############################################################
@pytest.fixture(autouse=True)
def allowlist(allowlist_factory, owner, origin_name):
    # Start registration
    allowlist_address = allowlist_factory.allowlistAddressByOriginName(origin_name)
    registration_started = allowlist_address != ZERO_ADDRESS
    if  registration_started == False:
        allowlist_factory.startProtocolRegistration(origin_name, {"from": owner})
    allowlist_address = allowlist_factory.allowlistAddressByOriginName(origin_name)
    assert allowlist_address != ZERO_ADDRESS
    allowlist = Contract(allowlist_address)
    assert allowlist.protocolOriginName() == origin_name

    # Add a spoof condition to allow registration to finish
    fake_condition = (
        "approve",
        ["address", "uint256"],
        [],
        "0xe0fc1e8a5F058024A0090ACaE5867C4E4617Ed15"
    )
    allowlist.addCondition(fake_condition, {"from": owner})
    number_of_registered_protocols_before = len(allowlist_factory.registeredProtocolsList())
    assert allowlist.conditionsLength() > 0

    # Finish registration
    protocol_registered = allowlist_factory.registeredProtocol(origin_name)
    if protocol_registered == False:
        allowlist_factory.finishProtocolRegistration(origin_name, {"from": owner})
        number_of_registered_protocols_after = len(allowlist_factory.registeredProtocolsList())
        assert number_of_registered_protocols_before + 1 == number_of_registered_protocols_after
    protocol_registered = allowlist_factory.registeredProtocol(origin_name)
    assert protocol_registered == True
    
    # Delete all conditions
    allowlist.deleteAllConditions({"from": owner})
    assert allowlist.conditionsLength() == 0
    
    # Return allowlist
    return Contract(allowlist_address)