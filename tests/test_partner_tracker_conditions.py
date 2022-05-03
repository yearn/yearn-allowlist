import pytest
from brownie import Contract, chain

MAX_UINT256 = 2**256-1

partner_tracker_address = "0x8ee392a4787397126C163Cb9844d7c447da419D8"
random_address = "0x83C8F28c26bF6aaca652Df1DbBE0e1b56F8baBa2"
vault_address = "0x5c0A86A32c129538D62C106Eb8115a8b02358d57"
partner_id_address = "0x3CE37278de6388532C3949ce4e886F365B14fB56"

@pytest.fixture
def implementation_id():
    return "IMPLEMENTATION_PARTNER_TRACKER"

@pytest.fixture
def partner_tracker():
    return Contract(partner_tracker_address)

@pytest.fixture(autouse=True)
def implementation(owner, AllowlistImplementationPartnerTracker, allowlist_addresses, allowlist, implementation_id):
    address_provider = Contract(allowlist_addresses["addresses_provider_address"])
    _implementation = AllowlistImplementationPartnerTracker.deploy(address_provider, {"from": owner})

    allowlist.setImplementation(implementation_id, _implementation, {"from": owner})
    return _implementation

def test_partner_tracker_address_validation(implementation):
    assert implementation.isPartnerTracker(random_address) == False
    assert implementation.isPartnerTracker(partner_tracker_address)

def test_is_vault(implementation):
    assert implementation.isVault(random_address) == False
    assert implementation.isVault(vault_address)

def test_deposit(allowlist, owner, partner_tracker, origin_name, allowlist_registry, implementation_id):
    chain.snapshot()

    encoded_data = partner_tracker.deposit.encode_input(vault_address, partner_id_address)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, partner_tracker.address, encoded_data)
    assert allowed == False

    # Add condition
    condition = (
        "PARTNER_TRACKER_DEPOSIT",
        implementation_id,
        "deposit",
        ["address", "address"],
        [
            ["target", "isPartnerTracker"], 
            ["param", "isVault", "0"]
        ]
    )
    allowlist.addCondition(condition, {"from": owner})

    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, partner_tracker.address, encoded_data)
    assert allowed

    chain.revert()

def test_deposit_with_amount(allowlist, owner, partner_tracker, origin_name, allowlist_registry, implementation_id):
    chain.snapshot()

    encoded_data = partner_tracker.deposit.encode_input(vault_address, partner_id_address, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, partner_tracker.address, encoded_data)
    assert allowed == False

    # Add condition
    condition = (
        "PARTNER_TRACKER_DEPOSIT_WITH_AMOUNT",
        implementation_id,
        "deposit",
        ["address", "address", "uint256"],
        [
            ["target", "isPartnerTracker"], 
            ["param", "isVault", "0"]
        ]
    )
    allowlist.addCondition(condition, {"from": owner})

    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, partner_tracker.address, encoded_data)
    assert allowed

    chain.revert()

def test_invalid_deposits(allowlist, owner, partner_tracker, origin_name, allowlist_registry, implementation_id):
    chain.snapshot()

    # Add condition
    condition = (
        "PARTNER_TRACKER_DEPOSIT",
        implementation_id,
        "deposit",
        ["address", "address"],
        [
            ["target", "isPartnerTracker"], 
            ["param", "isVault", "0"]
        ]
    )
    allowlist.addCondition(condition, {"from": owner})

    # incorrect vault address
    encoded_data = partner_tracker.deposit.encode_input(random_address, partner_id_address)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, partner_tracker.address, encoded_data)
    assert allowed == False

    # target address is not the parter tracker
    encoded_data = Contract(vault_address).deposit.encode_input(vault_address, partner_id_address)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, partner_tracker.address, encoded_data)
    assert allowed == False

    chain.revert()