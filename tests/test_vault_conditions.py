import pytest
from brownie import Contract, ZERO_ADDRESS, chain

MAX_UINT256 = 2**256-1

@pytest.fixture
def implementation(owner, YearnAllowlistImplementation, network_variables):
    registry_address = network_variables["registry_address"]
    return YearnAllowlistImplementation.deploy(registry_address, {"from": owner})

@pytest.fixture
def vault(network_variables):
    registry = Contract(network_variables["registry_address"])
    return Contract(registry.releases(0))

@pytest.fixture
def vault_token(vault):
    return Contract(vault.token())

##############################################################
# Tokens
##############################################################

# Token approvals

# Description: Normal vault token approval
# Signature: "token.approve(address,uint256)"
# Target: Must be a valid vault token
# Param 0: Must be a valid vault address
def test_vault_token_approval(allowlist_factory, allowlist, owner, origin_name, implementation, vault, vault_token):
    # Add condition
    condition = (
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata - token.approve(vault_address, UINT256_MAX)
    data = vault_token.approve.encode_input(vault, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault_token, data)
    assert allowed == True
    
    # Test invalid param - token.approve(not_vault_address, UINT256_MAX)
    data = vault_token.approve.encode_input(ZERO_ADDRESS, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault_token, data)
    assert allowed == False
    
    # Test invalid target - random_contract.approve(vault_address, UINT256_MAX)
    data = vault_token.approve.encode_input(vault, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, ZERO_ADDRESS, data)
    assert allowed == False
    
    # Test invalid method - token.decimals()
    data = vault_token.decimals.encode_input()
    allowed = allowlist_factory.validateCalldata(origin_name, vault_token, data)
    assert allowed == False
