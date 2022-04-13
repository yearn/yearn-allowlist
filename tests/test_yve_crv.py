import pytest
from brownie import Contract, ZERO_ADDRESS, chain, convert

MAX_UINT256 = 2**256-1

@pytest.fixture
def implementation_id():
    return "IMPLEMENTATION_YEARN_YVE_CRV"

@pytest.fixture
def crv():
    return Contract("0xD533a949740bb3306d119CC777fa900bA034cd52")

@pytest.fixture
def yve_crv():
    return Contract("0xc5bddf9843308380375a611c18b50fb9341f502a")

@pytest.fixture(autouse=True)
def implementation(owner, AllowlistImplementationYveCRV, allowlist_addresses, allowlist_registry, allowlist, implementation_id):
    use_live_contract = True

    _implementation = None
    if use_live_contract:
        key = "implementation_yearn_yve_crv"
        if key in allowlist_addresses:
            _implementation = Contract(allowlist_addresses[key])
    if _implementation == None:
        _implementation = AllowlistImplementationYveCRV.deploy({"from": owner})

    allowlist.setImplementation(implementation_id, _implementation, {"from": owner})
    return _implementation

# Description: CRV token approval to be used by yveCRV
# Signature: "token.approve(address,uint256)"
# Target: Must be the CRV token address
# Param 0: Must be the yveCRV token address
def test_crv_approval_for_yve_crv(allowlist_registry, allowlist, owner, origin_name, implementation_id, crv, yve_crv):
    chain.snapshot()

    # Add condition
    condition = (
        "CRV_APPROVE_YVE_CRV",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isCRV"], 
            ["param", "isYveCRV", "0"]
        ]
    )

    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata - crv.approve(yveCRV, UINT256_MAX)
    data = crv.approve.encode_input(yve_crv, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, crv, data)
    assert allowed == True
    
    # Test invalid param - crv.approve(not_yveCRV_address, UINT256_MAX)
    data = crv.approve.encode_input(ZERO_ADDRESS, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, crv, data)
    assert allowed == False
    
    # Test invalid target - random_contract.approve(yveCRV, UINT256_MAX)
    vault = Contract("0x5c0A86A32c129538D62C106Eb8115a8b02358d57")
    data = vault.approve.encode_input(vault, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, vault, data)
    assert allowed == False
    
    # Test invalid method - token.decimals()
    data = crv.decimals.encode_input()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, crv, data)
    assert allowed == False
    chain.revert()

# Description: Depositing (aka locking) into yveCRV
# Signature: "yveCRV.deposit(uint256)"
# Target: Must be the yveCRV token address
def test_yve_crv_deposit(allowlist_registry, allowlist, owner, origin_name, implementation_id, yve_crv):
    chain.snapshot()

    # Test deposit before adding condition - yveCRV.deposit(amount)
    data = yve_crv.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, yve_crv, data)
    assert allowed == False

    # Add condition
    condition = (
        "YVE_CRV_DEPSOIT",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "isYveCRV"]
        ]
    )

    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata - yveCRV.deposit(amount)
    data = yve_crv.deposit.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, yve_crv, data)
    assert allowed == True
   
    chain.revert()

# Description: Claiming yveCRV
# Signature: "yveCRV.claim()"
# Target: Must be the yveCRV token address
def test_yve_crv_claim(allowlist_registry, allowlist, owner, origin_name, implementation_id, yve_crv):
    chain.snapshot()

    # Test claim before adding condition - yveCRV.claim()
    data = yve_crv.claim.encode_input()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, yve_crv, data)
    assert allowed == False

    # Add condition
    condition = (
        "YVE_CRV_CLAIM",
        implementation_id,
        "claim",
        [],
        [
            ["target", "isYveCRV"]
        ]
    )

    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata - yveCRV.claim()
    data = yve_crv.claim.encode_input()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, yve_crv, data)
    assert allowed == True
   
    chain.revert()