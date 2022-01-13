import pytest
from brownie import Contract, ZERO_ADDRESS, chain
from brownie.convert import to_bytes

MAX_UINT256 = 2**256-1

@pytest.fixture
def implementation(owner, YearnVaultsAllowlistImplementation, network_variables, allowlist_factory):
    address_provider = Contract(network_variables["address_provider_address"])
    return YearnVaultsAllowlistImplementation.deploy(address_provider, allowlist_factory, {"from": owner})

@pytest.fixture
def registry_adapter(network_variables):
    address_provider = Contract(network_variables["address_provider_address"])
    return Contract(address_provider.addressById("REGISTRY_ADAPTER_V2_VAULTS"))

@pytest.fixture
def vault(registry_adapter):
    registry = Contract(registry_adapter.registryAddress())
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
def test_token_approval_for_vault(allowlist_factory, allowlist, owner, origin_name, implementation, vault, vault_token):
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
def test_token_approval_for_zap(allowlist_factory, allowlist, owner, network_variables, origin_name, implementation, vault_token):
    zap_in_to_vault_address_key = "zap_in_to_vault_address"
    if zap_in_to_vault_address_key not in network_variables:
        pytest.skip("no zap in address on this network")

    zap_in_contract = Contract(network_variables[zap_in_to_vault_address_key])

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

    # Test invalid param (before updating allowlist) - token.approve(zap_in_contract, UINT256_MAX)
    data = vault_token.approve.encode_input(zap_in_contract, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault_token, data)
    assert allowed == False

    # Set zapper contract addresse
    implementation.setIsZapInContract(zap_in_contract, True, {"from": owner})
    assert implementation.isZapInContract(zap_in_contract) == True

    # Test valid param (after adding to allowlist) - token.approve(zap_in_contract, UINT256_MAX)
    data = vault_token.approve.encode_input(zap_in_contract, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault_token, data)
    assert allowed == True

##############################################################
# Target: Vaults
##############################################################

# Vault deposits

# Description: Vault deposit
# Signature: "vault.deposit(uint256)"
# Target: Must be a valid vault address
def test_vault_deposit(allowlist_factory, allowlist, owner, origin_name, implementation, vault, vault_token):
    # Test deposit before adding condition - vault.deposit(amount)
    data = vault.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault, data)
    assert allowed == False
    
    # Add condition
    condition = (
        "deposit",
        ["uint256"],
        [
            ["target", "isVault"],
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata - vault.deposit(amount)
    data = vault.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault, data)
    assert allowed == True
    
# Vault withdrawals

# Signature: "vault.withdraw(uint256)"
# Target: Must be a valid vault address
def test_vault_withdraw(allowlist_factory, allowlist, owner, origin_name, implementation, vault, vault_token):
    # Test withdraw before adding condition - vault.withdraw(amount)
    data = vault.withdraw.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault, data)
    assert allowed == False
    
    # Add condition
    condition = (
        "withdraw",
        ["uint256"],
        [
            ["target", "isVault"],
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata - vault.withdraw(amount)
    data = vault.withdraw.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault, data)
    assert allowed == True

# Vault approvals

# Description: Vault zap out approval
# Signature: "vault.approve(address,uint256)"
# Target: Must be a valid vault address
# Param 0: Must be one of the following (mainnet):
#   - zapOut: "0xd6b88257e91e4E4D4E990B3A858c849EF2DFdE8c"
#   - Migrator contract(s)?
#     - trustedVaultMigrator: "0x1824df8D751704FA10FA371d62A37f9B8772ab90"
#     - triCryptoVaultMigrator: "0xC306a5ef4B990A7F2b3bC2680E022E6a84D75fC1"
def test_vault_zap_out_approval(allowlist_factory, allowlist, owner, origin_name, implementation, vault, vault_token, network_variables):
    # Zap out approvals
    zap_out_of_vault_address_key = "zap_out_of_vault_address"
    if zap_out_of_vault_address_key not in network_variables:
        pytest.skip("no zap out address on this network")

    zap_out_contract = Contract(network_variables[zap_out_of_vault_address_key])

    # Zap out condition
    condition = (
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVault"], 
            ["param", "isZapOutContract", "0"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})

    # Set zap out contract
    assert implementation.isZapOutContract(zap_out_contract) == False
    implementation.setIsZapOutContract(zap_out_contract, True, {"from": owner})
    assert implementation.isZapOutContract(zap_out_contract) == True

    # Test valid calldata - vault.approve(zap_out, UINT256_MAX)
    data = vault.approve.encode_input(zap_out_contract, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault, data)
    assert allowed == True

    # Test invalid target - invalid.approve(zap_out, UINT256_MAX)
    data = vault.approve.encode_input(zap_out_contract, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault_token, data)
    assert allowed == False

    # Test invalid param - vault.approve(not_zap, UINT256_MAX)
    not_zap = vault
    data = vault.approve.encode_input(not_zap, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault, data)
    assert allowed == False

# Description: Vault zap out approval
# Signature: "vault.approve(address,uint256)"
# Target: Must be a valid vault address
# Param 0: Must be one of the following (mainnet):
#   - trustedVaultMigrator: "0x1824df8D751704FA10FA371d62A37f9B8772ab90"
#   - triCryptoVaultMigrator: "0xC306a5ef4B990A7F2b3bC2680E022E6a84D75fC1"
def test_vault_migrator_approval(allowlist_factory, allowlist, owner, origin_name, implementation, vault, vault_token, network_variables):
    # Vault migrator approvals
    migrator_address_standard_key = "migrator_address_standard"
    if migrator_address_standard_key not in network_variables:
        pytest.skip("no standard migrator address on this network")

    migrator_address = network_variables[migrator_address_standard_key]

    # Migrator condition
    condition = (
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVault"], 
            ["param", "isMigratorContract", "0"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Set migrator contract
    implementation.setIsMigratorContract(migrator_address, True, {"from": owner})
    assert implementation.isMigratorContract(migrator_address) == True

    # Test valid calldata - vault.approve(migrator, UINT256_MAX)
    data = vault.approve.encode_input(migrator_address, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault, data)
    assert allowed == True

    # Test invalid target - invalid.approve(migrator, UINT256_MAX)
    data = vault.approve.encode_input(migrator_address, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault_token, data)
    assert allowed == False

    # Test invalid param - vault.approve(not_migrator, UINT256_MAX)
    not_migrator = vault
    data = vault.approve.encode_input(not_migrator, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, vault, data)
    assert allowed == False


##############################################################
# Target: Zaps
##############################################################

# Standard zap in

# Description: Zapping into a yVault
# Signature: "zapInContract.ZapIn(address,uint256,address,address,bool,uint256,address,address,bytes,address,bool)"
# Target 0: Must be a valid zap in contract (mainnet):
#   - zap_in_yearn_address: "0x92Be6ADB6a12Da0CA607F9d87DB2F9978cD6ec3E"
# Param 2: Must be a valid vault address
def test_zap_in_to_vault(allowlist_factory, allowlist, owner, origin_name, implementation, vault, network_variables):
    zap_in_to_vault_address_key = "zap_in_to_vault_address"
    if zap_in_to_vault_address_key not in network_variables:
        pytest.skip("no zap in address on this network")

    zap_in_contract = Contract(network_variables[zap_in_to_vault_address_key])

    # Set isZapInContract in implementation
    assert implementation.isZapInContract(zap_in_contract) == False
    implementation.setIsZapInContract(zap_in_contract, True, {"from": owner})
    assert implementation.isZapInContract(zap_in_contract) == True

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

# Standard zap out

# Description: Zapping out of a yVault
# Signature: "zapOutContract.ZapOut(address,uint256,address,bool,uint256,address,bytes,address,bool)"
# Target 0: Must be a valid zap out contract (mainnet):
#   - zap_out_yearn_address: "0xd6b88257e91e4E4D4E990B3A858c849EF2DFdE8c"
# Param 0: Must be a valid vault address
def test_zap_out_of_vault(allowlist_factory, allowlist, owner, origin_name, implementation, vault, network_variables):
    zap_out_of_vault_address_key = "zap_out_of_vault_address"
    if zap_out_of_vault_address_key not in network_variables:
        pytest.skip("no zap out address on this network")

    zap_out_contract = Contract(network_variables[zap_out_of_vault_address_key])

    # Set isZapOutContract in implementation
    assert implementation.isZapOutContract(zap_out_contract) == False
    implementation.setIsZapOutContract(zap_out_contract, True, {"from": owner})
    assert implementation.isZapOutContract(zap_out_contract) == True

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

    # Convenience function for generating the calldata inputted to the zap out contract.
    # Default parameters are for a zap out of a valid vault
    def makeZapOutData(zap_out_contract=zap_out_contract, vault=vault):
        return zap_out_contract.ZapOut.encode_input(
            vault,
            MAX_UINT256,
            ZERO_ADDRESS,
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
    
    # Test invalid target - trying to zap out using a contract that is not the zap out contract
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

# Pickle zap in

# Description: Zapping into a pickle vault
# Signature: "pickleZapContract.ZapIn(address,uint256,address,uint256,address,address,bytes,address)"
# Target 0: Must be a valid zap in contract (mainnet):
#   - zap_in_pickle_address: "0xc695f73c1862e050059367B2E64489E66c525983"
# Param 2: Must be the yvBOOST/ETH SLP pickle jar
def test_zap_in_to_pickle_jar(allowlist_factory, allowlist, owner, origin_name, implementation, vault, network_variables):
    zap_in_to_pickle_address_key = "zap_in_to_pickle_address"
    if zap_in_to_pickle_address_key not in network_variables:
        pytest.skip("no pickle jar zap in address on this network")
        
    pickle_jar_address = "pickle_jar_address"
    zap_in_contract = Contract(network_variables[zap_in_to_pickle_address_key])
    pickle_jar_contract = Contract(network_variables[pickle_jar_address])

    # Set isZapInContract for implementation
    assert implementation.isZapInContract(zap_in_contract) == False
    implementation.setIsZapInContract(zap_in_contract, True, {"from": owner})
    assert implementation.isZapInContract(zap_in_contract) == True

    # Set isPickleJarContract for implementation
    assert implementation.isPickleJarContract(pickle_jar_contract) == False
    implementation.setIsPickleJarContract(pickle_jar_contract, True, {"from": owner})    
    assert implementation.isPickleJarContract(pickle_jar_contract) == True

    # Add condition
    condition = (
        "ZapIn",
        ["address", "uint256", "address", "uint256", "address", "address", "bytes" ,"address"],
        [
            ["target", "isZapInContract"], 
            ["param", "isPickleJarContract", "2"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})

    # Convenience function for generating the calldata inputted to the zap in contract
    # Default parameters are for a zap into a valid pickle jar
    def makeZapInData(zap_in_contract=zap_in_contract, pickle_jar_contract=pickle_jar_contract):
        return zap_in_contract.ZapIn.encode_input(
            ZERO_ADDRESS,
            MAX_UINT256, 
            pickle_jar_contract,
            MAX_UINT256,
            ZERO_ADDRESS, 
            ZERO_ADDRESS, 
            to_bytes('0x0'), 
            ZERO_ADDRESS
        )
    
    # Test valid calldata - zapping into a valid vault
    data = makeZapInData()
    allowed = allowlist_factory.validateCalldata(origin_name, zap_in_contract, data)
    assert allowed == True
    
    # Test invalid param - zapping into a vault which isn't valid
    data = makeZapInData(pickle_jar_contract=ZERO_ADDRESS)
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

##############################################################
# Target: Migrators
##############################################################

# Migrations

# Description: Migrate tricrypto
# Signature: "tricrypto_migrator.migrate_to_new_vault()"
# Target: Must be valid migrator
def test_migrate_tricrypto(allowlist_factory, allowlist, owner, origin_name, implementation, network_variables):
    migrator_address_tricrypto_key = "migrator_address_tricrypto"
    if migrator_address_tricrypto_key not in network_variables:
        pytest.skip("no tricrypto migrator address on this network")

    tricrypto_migrator = Contract(network_variables[migrator_address_tricrypto_key])
    implementation.setIsMigratorContract(tricrypto_migrator, True, {"from": owner})
    
    # Test valid calldata before adding condition - tricrypto_migrator.migrate_to_new_vault()
    data = tricrypto_migrator.migrate_to_new_vault.encode_input()
    allowed = allowlist_factory.validateCalldata(origin_name, tricrypto_migrator, data)
    assert allowed == False

    # Add condition
    condition = (
        "migrate_to_new_vault",
        [],
        [
            ["target", "isMigratorContract"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - migrator.migrate_to_new_vault()
    data = tricrypto_migrator.migrate_to_new_vault.encode_input()
    allowed = allowlist_factory.validateCalldata(origin_name, tricrypto_migrator, data)
    assert allowed == True
    
    # Test valid calldata after removing migration contract - migrator.migrate_to_new_vault()
    implementation.setIsMigratorContract(tricrypto_migrator, False, {"from": owner})
    data = tricrypto_migrator.migrate_to_new_vault.encode_input()
    allowed = allowlist_factory.validateCalldata(origin_name, tricrypto_migrator, data)
    assert allowed == False
        
# Description: Standard migration
# Signature: "migrator.migrateAll(address,address)"
# Target: Must be valid migrator
# Param0: Must be a valid vault token
# Param1: Must be a valid vault token
def test_migrate_standard(allowlist_factory, allowlist, owner, origin_name, implementation, network_variables, vault):
    migrator_address_standard_key = "migrator_address_standard"
    if migrator_address_standard_key not in network_variables:
        pytest.skip("no standard migrator address on this network")

    migrator = Contract(network_variables[migrator_address_standard_key])
    implementation.setIsMigratorContract(migrator, True, {"from": owner})
    
    # Test valid calldata before adding condition - migrator.migrateAll(address,address)
    data = migrator.migrateAll.encode_input(vault, vault)
    allowed = allowlist_factory.validateCalldata(origin_name, migrator, data)
    assert allowed == False

    # Add condition
    condition = (
        "migrateAll",
        ["address", "address"],
        [
            ["target", "isMigratorContract"],
            ["param", "isVault", "0"],
            ["param", "isVault", "1"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - migrator.migrateAll(address,address)
    data = migrator.migrateAll.encode_input(vault, vault)
    allowed = allowlist_factory.validateCalldata(origin_name, migrator, data)
    assert allowed == True
    
    # Test valid calldata after removing migration contract - migrator.migrateAll(address,address)
    implementation.setIsMigratorContract(migrator, False, {"from": owner})
    data = migrator.migrateAll.encode_input(vault, vault)
    allowed = allowlist_factory.validateCalldata(origin_name, migrator, data)
    assert allowed == False
