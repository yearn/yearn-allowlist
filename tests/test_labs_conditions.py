import pytest
from brownie import Contract, ZERO_ADDRESS, chain

MAX_UINT256 = 2**256-1

@pytest.fixture
def implementation(owner, YearnLabsAllowlistImplementation):
    if chain.id != 1:
        pytest.skip('This test is not supported on chain ${chain.id}')

    return YearnLabsAllowlistImplementation.deploy({"from": owner})

##############################################################
# Target: Pickle Jar
##############################################################

# Deposit

# Description: Pickle jar deposit
# Signature: "pickle_jar.deposit(uint256)"
# Target: Must be the yveCRV/ETH SLP pickle jar
def test_pickle_jar_deposit(allowlist_factory, allowlist, owner, origin_name, implementation, network_variables):
    pickle_jar = Contract(network_variables["pickle_jar_address"])

    # Test valid calldata before adding condition - pickle_jar.deposit(UINT256_MAX)
    data = pickle_jar.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, pickle_jar, data)
    assert allowed == False

    # Add condition
    condition = (
        "deposit",
        ["uint256"],
        [
            ["target", "isPickleJar"], 
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - pickle_jar.deposit(UINT256_MAX)
    data = pickle_jar.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, pickle_jar, data)
    assert allowed == True
    
##############################################################
# Target: Pickle gauge
##############################################################

# Pickle gauge staking

# Description: Pickle jar deposit
# Signature: "pickle_jar.deposit(uint256)"
# Target: Must be the yveCRV/ETH SLP pickle jar
def test_pickle_gauge_stake(allowlist_factory, allowlist, owner, origin_name, implementation, network_variables):
    # Fetch pickle gauge
    pickle_gauge = Contract(network_variables["pickle_gauge_address"])

    # Test valid calldata before adding condition - pickle_gauge.deposit(UINT256_MAX)
    data = pickle_gauge.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, pickle_gauge, data)
    assert allowed == False

    # Add condition
    condition = (
        "deposit",
        ["uint256"],
        [
            ["target", "isPickleGauge"], 
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - pickle_gauge.deposit(UINT256_MAX)
    data = pickle_gauge.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, pickle_gauge, data)
    assert allowed == True
    
##############################################################
# Target: yveCRV-DAO yVault
##############################################################

# Locking

# Description: yveCRV vault lock
# Signature: "yvecrv.deposit(uint256)"
# Target: Must be yveCRV-DAO yVault
def test_yvecrv_lock(allowlist_factory, allowlist, owner, origin_name, implementation, network_variables):
    # Fetch yveCRV-DAO vault
    yvecrv_vault = Contract(network_variables["yvecrv_vault_address"])

    # Test valid calldata before adding condition - yveCrv.deposit(UINT256_MAX)
    data = yvecrv_vault.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, yvecrv_vault, data)
    assert allowed == False

    # Add condition
    condition = (
        "deposit",
        ["uint256"],
        [
            ["target", "isYveCrvVault"],
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - pickle_gauge.deposit(UINT256_MAX)
    data = yvecrv_vault.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, yvecrv_vault, data)
    assert allowed == True
    
# Claiming

# Description: yveCRV vault claim
# Signature: "yvecrv.claim()"
# Target: Must be yveCRV-DAO yVault
def test_yvecrv_claim(allowlist_factory, allowlist, owner, origin_name, implementation, network_variables):
    # Fetch yveCRV-DAO vault
    yvecrv_vault = Contract(network_variables["yvecrv_vault_address"])

    # Test valid calldata before adding condition - yveCrv.claim()
    data = yvecrv_vault.claim.encode_input()
    allowed = allowlist_factory.validateCalldata(origin_name, yvecrv_vault, data)
    assert allowed == False

    # Add condition
    condition = (
        "claim",
        [],
        [
            ["target", "isYveCrvVault"],
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - yvecrv_vault.claim()
    data = yvecrv_vault.claim.encode_input()
    allowed = allowlist_factory.validateCalldata(origin_name, yvecrv_vault, data)
    assert allowed == True
    
##############################################################
# Target: 3CRV zap
##############################################################

# Reinvest

# Description: Reinvest 3CRV into yveCRV-DAO vault
# Signature: "threecrv_zap.zap()"
# Target: Must be yearn 3CRV yveCRV-DAO zap contract
def test_threecrv_yvecrv_zap(allowlist_factory, allowlist, owner, origin_name, implementation, network_variables):
    # Fetch 3CRV zap contract
    threecrv_zap = Contract(network_variables["threecrv_zap_address"])

    # Test valid calldata before adding condition - yveCrv.deposit(UINT256_MAX)
    data = threecrv_zap.zap.encode_input()
    allowed = allowlist_factory.validateCalldata(origin_name, threecrv_zap, data)
    assert allowed == False

    # Add condition
    condition = (
        "zap",
        [],
        [
            ["target", "isThreeCrvZap"],
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - threecrv_zap.zap()
    data = threecrv_zap.zap.encode_input()
    allowed = allowlist_factory.validateCalldata(origin_name, threecrv_zap, data)
    assert allowed == True