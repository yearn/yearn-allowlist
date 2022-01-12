import pytest
from brownie import Contract, ZERO_ADDRESS, chain
from brownie.convert import to_bytes

MAX_UINT256 = 2**256-1

@pytest.fixture
def implementation(owner, YearnAllowlistImplementation, network_variables, allowlist_factory):
    registry_address = network_variables["registry_address"]
    return YearnAllowlistImplementation.deploy(registry_address, allowlist_factory, {"from": owner})

@pytest.fixture
def vault(network_variables):
    registry = Contract(network_variables["registry_address"])
    return Contract(registry.releases(0))

@pytest.fixture
def vault_token(vault):
    return Contract(vault.token())

##############################################################
# Target: Tokens
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
            ["target", "isVaultUnderlyingToken"], 
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

# Description: Token approvals for vault zaps
# Signature: "token.approve(address,uint256)"
# Target: Must be a valid vault token
# Param 0: Must be one of the following (mainnet):
#   - zap_in_yearn_address: "0x92Be6ADB6a12Da0CA607F9d87DB2F9978cD6ec3E"
#   - zap_in_pickle_address: "0xc695f73c1862e050059367B2E64489E66c525983"
#   - another address on the custom 
def test_vault_token_zap_approval(allowlist_factory, allowlist, owner, network_variables, origin_name, implementation, vault, vault_token):
    # This test is not supported on all networks
    test_supported = "vault_zap_in_addresses" in network_variables
    if (test_supported == False):
        return
    zap_contracts_addresses = network_variables["vault_zap_in_addresses"]

    # Add condition
    condition = (
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultUnderlyingToken"],
            ["param", "isZapInContract", "0"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})

    # Test invalid param (before updating allowlist) - token.approve(zap_contracts_addresses[0], UINT256_MAX)
    data = vault_token.approve.encode_input(zap_contracts_addresses[0], MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault_token, data)
    assert allowed == False

    # Set zapper contract addresses
    for zap_contract_address in zap_contracts_addresses:
        implementation.setIsZapInContract(zap_contract_address, True, {"from": owner})
        assert implementation.isZapInContract(zap_contract_address) == True

    # Test valid param (after adding to allowlist) - token.approve(zap_contracts_addresses[i], UINT256_MAX)
    for zap_contract_address in zap_contracts_addresses:
        data = vault_token.approve.encode_input(zap_contract_address, MAX_UINT256)
        allowed = allowlist_factory.validateCalldata(origin_name, vault_token, data)
        assert allowed == True


##############################################################
# Target: Zaps
##############################################################

# Description: Zapping into a yVault
# Signature: "zapInContract.ZapIn(address,uint256,address,address,bool,uint256,address,address,bytes,address,bool)"
# Target 0: Must be a valid zap in contract (mainnet):
#   - zap_in_yearn_address: "0x92Be6ADB6a12Da0CA607F9d87DB2F9978cD6ec3E"
#   - zap_in_pickle_address: "0xc695f73c1862e050059367B2E64489E66c525983"
# Param 2: Must be a valid vault address
def test_vault_zap_in(allowlist_factory, allowlist, owner, origin_name, implementation, vault, network_variables):
    # This test is not supported on all networks
    test_supported = "vault_zap_in_addresses" in network_variables
    if (test_supported == False):
        return
    zap_contracts_addresses = network_variables["vault_zap_in_addresses"]

    # We need to manually set the addresses which are yearn zapper contracts on the implementation.
    # In production these should be the contracts for: yVault zap in, Pickle jar zap in
    for zap_contract_address in zap_contracts_addresses:
        implementation.setIsZapInContract(zap_contract_address, True, {"from": owner})
        assert implementation.isZapInContract(zap_contract_address) == True

    # Add condition
    condition = (
        "ZapIn",
        ["address", "uint256", "address", "address", "bool", "uint256", "address", "address", "bytes", "address", "bool"],
        [
            ["target", "isZapInContract"], 
            ["param", "isVault", "2"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})

    # Set sample zap in contract for testing
    zap_in_contract = Contract(zap_contracts_addresses[0])

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
    implementation.setIsZapInContract(zap_in_contract, False, {"from": owner})
    assert implementation.isZapInContract(zap_in_contract) == False

    # Test that the target validation fails, as the zapper contract address is no longer recognized by the implementation 
    data = makeZapInData()
    allowed = allowlist_factory.validateCalldata(origin_name, zap_in_contract, data)
    assert allowed == False


# Description: Zapping out of a yVault
# Signature: "zapOutContract.ZapOut(address,uint256,address,bool,uint256,address,bytes,address,bool)"
# Target 0: Must be a valid zap out contract (mainnet):
#   - zap_out_yearn_address: "0xd6b88257e91e4E4D4E990B3A858c849EF2DFdE8"
# Param 0: Must be a valid vault address
def test_vault_zap_out(allowlist_factory, allowlist, owner, origin_name, implementation, vault, network_variables):
    # This test is not supported on all networks
    test_supported = "vault_zap_out_addresses" in network_variables
    if (test_supported == False):
        return
    zap_contracts_addresses = network_variables["vault_zap_out_addresses"]

    # We need to manually set the addresses which are yearn zapper contracts on the implementation.
    # In production these should be the contract for yVault zap out
    for zap_contract_address in zap_contracts_addresses:
        implementation.setIsZapOutContract(zap_contract_address, True, {"from": owner})
        assert implementation.isZapOutContract(zap_contract_address) == True

    # Add condition
    condition = (
        "ZapOut",
        ["address", "uint256", "address", "bool", "uint256", "address", "bytes", "address", "bool"],
        [
            ["target", "isZapOutContract"], 
            ["param", "isVault", "0"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})

    # Set sample zap out contract for testing
    zap_out_contract = Contract(zap_contracts_addresses[0])

    # Convenience function for generating the calldata inputted to the zap out contract.
    # Default parameters are for a zap out of a valid vault
    def makeZapOutData(zap_out_contract=zap_out_contract, vault=vault):
        return zap_out_contract.ZapOut.encode_input(
            vault, 
            MAX_UINT256, 
            vault, 
            False, 
            MAX_UINT256, 
            ZERO_ADDRESS, 
            to_bytes('0x0'), 
            ZERO_ADDRESS, 
            False
        )
    
    # Test valid calldata - zapping out of a valid vault
    data = makeZapOutData()
    allowed = allowlist_factory.validateCalldata(origin_name, zap_out_contract, data)
    assert allowed == True
    
    # Test invalid param - zapping out of a vault which isn't valid
    data = makeZapOutData(vault=ZERO_ADDRESS)
    allowed = allowlist_factory.validateCalldata(origin_name, zap_out_contract, data)
    assert allowed == False
    
    # Test invalid target - trying to zap out of a vault using a contract that is not a zap out contract
    data = makeZapOutData()
    allowed = allowlist_factory.validateCalldata(origin_name, vault, data)
    assert allowed == False

    # Disable the implementation recognizing that the zap_out_contract is a valid zapper address
    implementation.setIsZapOutContract(zap_out_contract, False, {"from": owner})
    assert implementation.isZapOutContract(zap_out_contract) == False

    # Test that the target validation fails, as the zapper contract address is no longer recognized by the implementation 
    data = makeZapOutData()
    allowed = allowlist_factory.validateCalldata(origin_name, zap_out_contract, data)
    assert allowed == False