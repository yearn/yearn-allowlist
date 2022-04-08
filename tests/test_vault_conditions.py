import pytest
from brownie import Contract, ZERO_ADDRESS, chain, convert

MAX_UINT256 = 2**256-1

@pytest.fixture
def implementation_id():
    return "IMPLEMENTATION_YEARN_VAULTS"

@pytest.fixture(autouse=True)
def implementation(owner, AllowlistImplementationYearnVaults, allowlist_addresses, allowlist_registry, allowlist, implementation_id):
    use_live_contract = True

    _implementation = None
    if use_live_contract:
        key = "implementation_yearn_vaults_address"
        if key in allowlist_addresses:
            _implementation = Contract(allowlist_addresses[key])
    if _implementation == None:
        address_provider = Contract(allowlist_addresses["addresses_provider_address"])
        _implementation = AllowlistImplementationYearnVaults.deploy(address_provider, allowlist_registry, {"from": owner})

    allowlist.setImplementation(implementation_id, _implementation, {"from": owner})
    return _implementation

@pytest.fixture
def registry_adapter(allowlist_addresses):
    address_provider = Contract(allowlist_addresses["addresses_provider_address"])
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
def test_token_approval_for_vault(allowlist_registry, allowlist, owner, origin_name, implementation_id, vault, vault_token):
    chain.snapshot()
    # Add condition
    condition = (
        "TOKEN_APPROVE_VAULT",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultUnderlyingToken"], 
            ["param", "isVault", "0"]
        ]
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata - token.approve(vault_address, UINT256_MAX)
    data = vault_token.approve.encode_input(vault, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault_token, data)
    assert allowed == True
    
    # Test invalid param - token.approve(not_vault_address, UINT256_MAX)
    data = vault_token.approve.encode_input(ZERO_ADDRESS, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault_token, data)
    assert allowed == False
    
    # Test invalid target - random_contract.approve(vault_address, UINT256_MAX)
    data = vault_token.approve.encode_input(vault, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, ZERO_ADDRESS, data)
    assert allowed == False
    
    # Test invalid method - token.decimals()
    data = vault_token.decimals.encode_input()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault_token, data)
    assert allowed == False
    chain.revert()

# Description: Token approvals for vault zaps
# Signature: "token.approve(address,uint256)"
# Target: Must be a valid vault token
# Param 0: Must be one of the following (mainnet):
#   - zap_in_yearn_address: "0x92Be6ADB6a12Da0CA607F9d87DB2F9978cD6ec3E"
#   - zap_in_pickle_address: "0xc695f73c1862e050059367B2E64489E66c525983"
#   - another address on the custom 
def test_token_approval_for_zap(allowlist_registry, allowlist, owner, allowlist_addresses, origin_name, implementation_id, vault_token, implementation):
    chain.snapshot()
    # This test is not supported on all networks
    test_supported = "zap_in_to_vault_address" in allowlist_addresses
    if (chain.id == 1):
        assert test_supported == True
    if (test_supported == False):
        return
    zap_in_contract = Contract(allowlist_addresses["zap_in_to_vault_address"])

    # Add condition
    condition = (
        "TOKEN_APPROVE_ZAP",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultUnderlyingToken"],
            ["param", "isZapInContract", "0"]
        ]
    )
    allowlist.addCondition(condition, {"from": owner})

    # Test invalid param (before updating allowlist) - token.approve(zap_in_contract, UINT256_MAX)
    data = vault_token.approve.encode_input(zap_in_contract, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault_token, data)
    assert allowed == False

    # Set zapper contract addresse
    implementation.setIsZapInContract(zap_in_contract, True, {"from": owner})
    assert implementation.isZapInContract(zap_in_contract) == True

    # Test valid param (after adding to allowlist) - token.approve(zap_in_contract, UINT256_MAX)
    data = vault_token.approve.encode_input(zap_in_contract, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault_token, data)
    assert allowed == True

    chain.revert()

##############################################################
# Target: Vaults
##############################################################

# Vault deposits

# Description: Vault deposit
# Signature: "vault.deposit(uint256)"
# Target: Must be a valid vault address
def test_vault_deposit(allowlist_registry, allowlist, owner, origin_name, implementation_id, vault):
    chain.snapshot()
    # Test deposit before adding condition - vault.deposit(amount)
    data = vault.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
    assert allowed == False
    
    # Add condition
    condition = (
        "VAULT_DEPOST",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "isVault"],
        ]
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata - vault.deposit(amount)
    data = vault.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
    assert allowed == True
    chain.revert()
    
# Vault withdrawals

# Signature: "vault.withdraw(uint256)"
# Target: Must be a valid vault address
def test_vault_withdraw(allowlist_registry, allowlist, owner, origin_name, implementation_id, vault):
    chain.snapshot()
    # Test withdraw before adding condition - vault.withdraw(amount)
    data = vault.withdraw.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
    assert allowed == False
    
    # Add condition
    condition = (
        "VAULT_WITHDRAW",
        implementation_id,
        "withdraw",
        ["uint256"],
        [
            ["target", "isVault"],
        ]
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata - vault.withdraw(amount)
    data = vault.withdraw.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
    assert allowed == True
    chain.revert()

# Vault approvals

# Description: Vault zap out approval
# Signature: "vault.approve(address,uint256)"
# Target: Must be a valid vault address
# Param 0: Must be one of the following (mainnet):
#   - zapOut: "0xd6b88257e91e4E4D4E990B3A858c849EF2DFdE8c"
#   - Migrator contract(s)?
#     - trustedVaultMigrator: "0x1824df8D751704FA10FA371d62A37f9B8772ab90"
#     - triCryptoVaultMigrator: "0xC306a5ef4B990A7F2b3bC2680E022E6a84D75fC1"
def test_vault_zap_out_approval(allowlist_registry, allowlist, owner, origin_name, implementation, implementation_id, vault, vault_token, allowlist_addresses):
    chain.snapshot()
    # Zap out approvals
    zap_out_of_vault_address = "zap_out_of_vault_address"
    test_supported = zap_out_of_vault_address in allowlist_addresses
    if (chain.id == 1):
        assert test_supported == True

    if test_supported:
        zap_out_contract = Contract(allowlist_addresses[zap_out_of_vault_address])

        # Zap out condition
        condition = (
            "VAULT_APPROVE_ZAP",
            implementation_id,
            "approve",
            ["address", "uint256"],
            [
                ["target", "isVault"], 
                ["param", "isZapOutContract", "0"]
            ]
        )
        allowlist.addCondition(condition, {"from": owner})

        # Set zap out contract
        assert implementation.isZapOutContract(zap_out_contract) == False
        implementation.setIsZapOutContract(zap_out_contract, True, {"from": owner})
        assert implementation.isZapOutContract(zap_out_contract) == True

        # Test valid calldata - vault.approve(zap_out, UINT256_MAX)
        data = vault.approve.encode_input(zap_out_contract, MAX_UINT256)
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
        assert allowed == True

        # Test invalid target - invalid.approve(zap_out, UINT256_MAX)
        data = vault.approve.encode_input(zap_out_contract, MAX_UINT256)
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault_token, data)
        assert allowed == False

        # Test invalid param - vault.approve(not_zap, UINT256_MAX)
        not_zap = vault
        data = vault.approve.encode_input(not_zap, MAX_UINT256)
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
        assert allowed == False

    migrator_address_standard = "migrator_address_standard"
    test_supported = migrator_address_standard in allowlist_addresses
    if (chain.id == 1):
        assert test_supported == True
    
    chain.revert()

# Description: Vault zap out approval
# Signature: "vault.approve(address,uint256)"
# Target: Must be a valid vault address
# Param 0: Must be one of the following (mainnet):
#   - trustedVaultMigrator: "0x1824df8D751704FA10FA371d62A37f9B8772ab90"
#   - triCryptoVaultMigrator: "0xC306a5ef4B990A7F2b3bC2680E022E6a84D75fC1"
def test_vault_migrator_approval(allowlist_registry, allowlist, owner, origin_name, implementation, implementation_id, vault, vault_token, allowlist_addresses):
    chain.snapshot()
    # Vault migrator approvals
    migrator_address_standard = "migrator_address_standard"
    test_supported = migrator_address_standard in allowlist_addresses
    if (chain.id == 1):
        assert test_supported == True

    # Migration approvals
    if test_supported:
        migrator_address = allowlist_addresses[migrator_address_standard]

        # Migrator condition
        condition = (
            "VAULT_APPROVE_MIGRATOR",
            implementation_id,
            "approve",
            ["address", "uint256"],
            [
                ["target", "isVault"], 
                ["param", "isMigratorContract", "0"]
            ]
        )
        allowlist.addCondition(condition, {"from": owner})
        
        # Set migrator contract
        implementation.setIsMigratorContract(migrator_address, True, {"from": owner})
        assert implementation.isMigratorContract(migrator_address) == True

        # Test valid calldata - vault.approve(migrator, UINT256_MAX)
        data = vault.approve.encode_input(migrator_address, MAX_UINT256)
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
        assert allowed == True

        # Test invalid target - invalid.approve(migrator, UINT256_MAX)
        data = vault.approve.encode_input(migrator_address, MAX_UINT256)
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault_token, data)
        assert allowed == False

        # Test invalid param - vault.approve(not_migrator, UINT256_MAX)
        not_migrator = vault
        data = vault.approve.encode_input(not_migrator, MAX_UINT256)
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
        assert allowed == False
    
    chain.revert()


##############################################################
# Target: Zaps
##############################################################

# Standard zap in

# Description: Zapping into a yVault
# Signature: "zapInContract.ZapIn(address,uint256,address,address,bool,uint256,address,address,bytes,address,bool)"
# Target 0: Must be a valid zap in contract (mainnet):
#   - zap_in_yearn_address: "0x92Be6ADB6a12Da0CA607F9d87DB2F9978cD6ec3E"
# Param 2: Must be a valid vault address
def test_zap_in_to_vault(allowlist_registry, allowlist, owner, origin_name, implementation, implementation_id, vault, allowlist_addresses):
    chain.snapshot()
    # This test is not supported on all networks
    zap_in_to_vault_address = "zap_in_to_vault_address"
    test_supported = zap_in_to_vault_address in allowlist_addresses
    if (test_supported == False):
        return
    zap_in_contract = Contract(allowlist_addresses[zap_in_to_vault_address])

    # Set isZapInContract in implementation
    assert implementation.isZapInContract(zap_in_contract) == False
    implementation.setIsZapInContract(zap_in_contract, True, {"from": owner})
    assert implementation.isZapInContract(zap_in_contract) == True

    # Add condition
    condition = (
        "ZAP_IN_TO_VAULT",
        implementation_id,
        "ZapIn",
        ["address", "uint256", "address", "address", "bool", "uint256", "address", "address", "bytes", "address", "bool"],
        [
            ["target", "isZapInContract"], 
            ["param", "isVault", "2"]
        ]
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
            convert.to_bytes('0x0'), 
            ZERO_ADDRESS, 
            False
        )
    
    # Test valid calldata - zapping into a valid vault
    data = makeZapInData()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, zap_in_contract, data)
    assert allowed == True
    
    # Test invalid param - zapping into a vault which isn't valid
    data = makeZapInData(vault=ZERO_ADDRESS)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, zap_in_contract, data)
    assert allowed == False
    
    # Test invalid target - trying to zap in using a contract that is not the zap in contract
    data = makeZapInData()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
    assert allowed == False

    # Disable the implementation recognizing that the zap_in_contract is a valid zapper address
    implementation.setIsZapInContract(zap_in_contract, False, {"from": owner})
    assert implementation.isZapInContract(zap_in_contract) == False

    # Test that the target validation fails, as the zapper contract address is no longer recognized by the implementation 
    data = makeZapInData()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, zap_in_contract, data)
    assert allowed == False

    chain.revert()

# Standard zap out

# Description: Zapping out of a yVault
# Signature: "zapOutContract.ZapOut(address,uint256,address,bool,uint256,address,bytes,address,bool)"
# Target 0: Must be a valid zap out contract (mainnet):
#   - zap_out_yearn_address: "0xd6b88257e91e4E4D4E990B3A858c849EF2DFdE8c"
# Param 0: Must be a valid vault address
def test_zap_out_of_vault(allowlist_registry, allowlist, owner, origin_name, implementation, implementation_id, vault, allowlist_addresses):
    chain.snapshot()
    # This test is not supported on all networks
    zap_out_of_vault_address = "zap_out_of_vault_address"
    test_supported = zap_out_of_vault_address in allowlist_addresses
    if (chain.id == 1):
        assert test_supported == True
    if (test_supported == False):
        return
    zap_out_contract = Contract(allowlist_addresses[zap_out_of_vault_address])

    # Set isZapOutContract in implementation
    assert implementation.isZapOutContract(zap_out_contract) == False
    implementation.setIsZapOutContract(zap_out_contract, True, {"from": owner})
    assert implementation.isZapOutContract(zap_out_contract) == True

    # Add condition
    condition = (
        "ZAP_OUT_OF_VAULT",
        implementation_id,
        "ZapOut",
        ["address", "uint256", "address", "bool", "uint256", "address", "bytes", "address", "bool"],
        [
            ["target", "isZapOutContract"], 
            ["param", "isVault", "0"]
        ]
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
            convert.to_bytes('0x0'),
            ZERO_ADDRESS,
            False
        )
    
    # Test valid calldata - zapping out of a valid vault
    data = makeZapOutData()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, zap_out_contract, data)
    assert allowed == True
    
    # Test invalid param - zapping out of a vault which isn't valid
    data = makeZapOutData(vault=ZERO_ADDRESS)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, zap_out_contract, data)
    assert allowed == False
    
    # Test invalid target - trying to zap out using a contract that is not the zap out contract
    data = makeZapOutData()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
    assert allowed == False

    # Disable the implementation recognizing that the zap_out_contract is a valid zapper address
    implementation.setIsZapOutContract(zap_out_contract, False, {"from": owner})
    assert implementation.isZapOutContract(zap_out_contract) == False

    # Test that the target validation fails, as the zapper contract address is no longer recognized by the implementation 
    data = makeZapOutData()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, zap_out_contract, data)
    assert allowed == False

    chain.revert()

# Pickle zap in

# Description: Zapping into a pickle vault
# Signature: "pickleZapContract.ZapIn(address,uint256,address,uint256,address,address,bytes,address)"
# Target 0: Must be a valid zap in contract (mainnet):
#   - zap_in_pickle_address: "0xc695f73c1862e050059367B2E64489E66c525983"
# Param 2: Must be the yvBOOST/ETH SLP pickle jar
def test_zap_in_to_pickle_jar(allowlist_registry, allowlist, owner, origin_name, implementation, implementation_id, vault, allowlist_addresses):
    chain.snapshot()
    # This test is not supported on all networks
    zap_in_to_pickle_address = "zap_in_to_pickle_address"
    pickle_jar_address = "pickle_jar_address"
    test_supported = zap_in_to_pickle_address in allowlist_addresses and pickle_jar_address in allowlist_addresses
    if (chain.id == 1):
        assert test_supported == True
    if (test_supported == False):
        return
    zap_in_contract = Contract(allowlist_addresses[zap_in_to_pickle_address])
    pickle_jar_contract = Contract(allowlist_addresses[pickle_jar_address])

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
        "ZAP_IN_TO_PICKLE_JAR",
        implementation_id,
        "ZapIn",
        ["address", "uint256", "address", "uint256", "address", "address", "bytes" ,"address"],
        [
            ["target", "isZapInContract"], 
            ["param", "isPickleJarContract", "2"]
        ]
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
            convert.to_bytes('0x0'), 
            ZERO_ADDRESS
        )
    
    # Test valid calldata - zapping into a valid vault
    data = makeZapInData()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, zap_in_contract, data)
    assert allowed == True
    
    # Test invalid param - zapping into a vault which isn't valid
    data = makeZapInData(pickle_jar_contract=ZERO_ADDRESS)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, zap_in_contract, data)
    assert allowed == False
    
    # Test invalid target - trying to zap in using a contract that is not the zap in contract
    data = makeZapInData()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
    assert allowed == False

    # Disable the implementation recognizing that the zap_in_contract is a valid zapper address
    implementation.setIsZapInContract(zap_in_contract, False, {"from": owner})
    assert implementation.isZapInContract(zap_in_contract) == False

    # Test that the target validation fails, as the zapper contract address is no longer recognized by the implementation 
    data = makeZapInData()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, zap_in_contract, data)
    assert allowed == False

    chain.revert()

##############################################################
# Target: Migrators
##############################################################

# Migrations

# Description: Migrate tricrypto
# Signature: "tricrypto_migrator.migrate_to_new_vault()"
# Target: Must be valid migrator
def test_migrate_tricrypto(allowlist_registry, allowlist, owner, origin_name, implementation, implementation_id, allowlist_addresses):
    chain.snapshot()
    if "migrator_address_tricrypto" in allowlist_addresses:
        tricrypto_migrator = Contract(allowlist_addresses["migrator_address_tricrypto"])
        implementation.setIsMigratorContract(tricrypto_migrator, True, {"from": owner})
        
        # Test valid calldata before adding condition - tricrypto_migrator.migrate_to_new_vault()
        data = tricrypto_migrator.migrate_to_new_vault.encode_input()
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, tricrypto_migrator, data)
        assert allowed == False

        # Add condition
        condition = (
            "MIGRATE_VAULT_TRICRYPTO",
            implementation_id,
            "migrate_to_new_vault",
            [],
            [
                ["target", "isMigratorContract"]
            ]
        )
        allowlist.addCondition(condition, {"from": owner})
        
        # Test valid calldata after adding condition - migrator.migrate_to_new_vault()
        data = tricrypto_migrator.migrate_to_new_vault.encode_input()
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, tricrypto_migrator, data)
        assert allowed == True
        
        # Test valid calldata after removing migration contract - migrator.migrate_to_new_vault()
        implementation.setIsMigratorContract(tricrypto_migrator, False, {"from": owner})
        data = tricrypto_migrator.migrate_to_new_vault.encode_input()
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, tricrypto_migrator, data)
        assert allowed == False

    chain.revert()
        
# Description: Standard migration
# Signature: "migrator.migrateAll(address,address)"
# Target: Must be valid migrator
# Param0: Must be a valid vault token
# Param1: Must be a valid vault token
def test_migrate_standard(allowlist_registry, allowlist, owner, origin_name, implementation, implementation_id, allowlist_addresses, vault):
    chain.snapshot()
    if "migrator_address_standard" in allowlist_addresses:
        migrator = Contract(allowlist_addresses["migrator_address_standard"])
        implementation.setIsMigratorContract(migrator, True, {"from": owner})
        
        # Test valid calldata before adding condition - migrator.migrateAll(address,address)
        data = migrator.migrateAll.encode_input(vault, vault)
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, migrator, data)
        assert allowed == False

        # Add condition
        condition = (
            "MIGRATE_VAULT_V2",
            implementation_id,
            "migrateAll",
            ["address", "address"],
            [
                ["target", "isMigratorContract"],
                ["param", "isVault", "0"],
                ["param", "isVault", "1"]
            ]
        )
        allowlist.addCondition(condition, {"from": owner})
        
        # Test valid calldata after adding condition - migrator.migrateAll(address,address)
        data = migrator.migrateAll.encode_input(vault, vault)
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, migrator, data)
        assert allowed == True
        
        # Test valid calldata after removing migration contract - migrator.migrateAll()
        implementation.setIsMigratorContract(migrator, False, {"from": owner})
        data = migrator.migrateAll.encode_input(vault, vault)
        allowed = allowlist_registry.validateCalldataByOrigin(origin_name, migrator, data)
        assert allowed == False
    
    chain.revert()

def test_conditions_json(allowlist):
    all_conditions_json = allowlist.conditionsJson()
    assert(len(all_conditions_json) > 0)

    #####################################################################################
    # Notice: You can print the entire JSON for this test if you uncomment the line below
    #####################################################################################
    # print(all_conditions_json)
