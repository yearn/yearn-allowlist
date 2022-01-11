import pytest
from brownie import Contract, ZERO_ADDRESS, chain
from brownie.convert import to_bytes

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

@pytest.fixture
def zap_in_contract():
    return Contract("0x92Be6ADB6a12Da0CA607F9d87DB2F9978cD6ec3E")

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


# Description: Approval of the yearn zap in contract
# Signature: "zapInContract.ZapIn(address,uint256,address,address,bool,uint256,address,address,bytes,address,bool)"
# Target: Must be the zap in contract, which is 0x92Be6ADB6a12Da0CA607F9d87DB2F9978cD6ec3E
# Param 2: Must be a valid vault address
def test_zap_in(allowlist_factory, allowlist, owner, origin_name, implementation, vault, vault_token, zap_in_contract):
    # We need to manually set the addresses which are yearn zapper contracts on the implementation.
    # These should be the contracts for: yVault zap in, yVault zap out, Pickle jar zap in
    implementation.setIsZapperContract(zap_in_contract, True, {"from": owner})
    assert implementation.isZapperContract(zap_in_contract) == True

    # Add condition
    condition = (
        "ZapIn",
        ["address", "uint256", "address", "address", "bool", "uint256", "address", "address", "bytes", "address", "bool"],
        [
            ["target", "isZapperContract"], 
            ["param", "isVault", "2"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})

    # Convenience function for generating the calldata inputted to the zap in contract.
    # Default parameters are for a zap into a valid vault
    def makeZapInData(zap_in_contract=zap_in_contract, vault=vault):
        return zap_in_contract.ZapIn.encode_input(
            ZERO_ADDRESS, 
            MAX_UINT256, 
            vault, 
            ZERO_ADDRESS, 
            False, 
            MAX_UINT256, 
            ZERO_ADDRESS, 
            ZERO_ADDRESS, 
            to_bytes('0x0'), 
            ZERO_ADDRESS, 
            False
        )
    
    # Test valid calldata - zapping into a valid vault
    data = makeZapInData()
    allowed = allowlist_factory.validateCalldata(origin_name, zap_in_contract, data)
    assert allowed == True
    
    # Test invalid param - zapping into a vault which isn't valid
    data = makeZapInData(vault=ZERO_ADDRESS)
    allowed = allowlist_factory.validateCalldata(origin_name, zap_in_contract, data)
    assert allowed == False
    
    # Test invalid target - trying to zap in using a contract that is not the zap in contract
    data = makeZapInData()
    allowed = allowlist_factory.validateCalldata(origin_name, vault, data)
    assert allowed == False

    # Disable the implementation recognizing that the zap_in_contract is a valid zapper address
    implementation.setIsZapperContract(zap_in_contract, False, {"from": owner})
    assert implementation.isZapperContract(zap_in_contract) == False

    # Test that the target validation fails, as the zapper contract address is no longer recognized by the implementation 
    data = makeZapInData()
    allowed = allowlist_factory.validateCalldata(origin_name, zap_in_contract, data)
    assert allowed == False