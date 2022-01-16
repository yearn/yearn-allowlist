import pytest
from brownie import Contract, ZERO_ADDRESS, chain
MAX_UINT256 = 2**256-1

@pytest.fixture
def implementation_id():
    return "IMPLEMENTATION_IRON_BANK"

@pytest.fixture(autouse=True)
def implementation(owner, AllowlistImplementationIronBank, address_provider, allowlist, implementation_id, allowlist_addresses):
    use_live_contract = True

    _implementation = None
    if use_live_contract:
        key = "implementation_iron_bank_address"
        if key in allowlist_addresses:
            _implementation = Contract(allowlist_addresses[key])
    if _implementation == None:
        address_provider = Contract(allowlist_addresses["addresses_provider_address"])
        _implementation = AllowlistImplementationIronBank.deploy(address_provider, {"from": owner})

    allowlist.setImplementation(implementation_id, _implementation, {"from": owner})
    return _implementation

@pytest.fixture
def market(registry_adapter):
    return Contract(registry_adapter.assetsAddresses()[0])

@pytest.fixture
def registry_adapter(address_provider):
    return Contract(address_provider.addressById("REGISTRY_ADAPTER_IRON_BANK"))

@pytest.fixture
def comptroller_proxy(registry_adapter):
    return Contract(registry_adapter.comptrollerAddress())

@pytest.fixture
def comptroller_implementation(comptroller_proxy):
    return Contract(comptroller_proxy.comptrollerImplementation())

@pytest.fixture
def market_token(market):
    return Contract(market.underlying())

##############################################################
# Target: Tokens
##############################################################

# Token approvals

# Description: Normal vault token approval
# Signature: "token.approve(address,uint256)"
# Target: Must be a valid iron bank underlying token
# Param 0: Must be a valid iron bank market
def test_token_approval_for_market(allowlist_registry, allowlist, owner, origin_name, condition_by_id, market, market_token):
    # Add condition
    condition = condition_by_id("TOKEN_APPROVE_MARKET")
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata - token.approve(market, UINT256_MAX)
    data = market_token.approve.encode_input(market, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market_token, data)
    assert allowed == True
    
    # Test invalid param - token.approve(not_market, UINT256_MAX)
    data = market_token.approve.encode_input(ZERO_ADDRESS, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market_token, data)
    assert allowed == False
    
    # Test invalid target - random_contract.approve(market, UINT256_MAX)
    data = market_token.approve.encode_input(market, MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, ZERO_ADDRESS, data)
    assert allowed == False
    
    # Test invalid method - token.decimals()
    data = market_token.decimals.encode_input()
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market_token, data)
    assert allowed == False

##############################################################
# Target: Markets
##############################################################

# Supply

# Description: Market supply
# Signature: "market.mint(uint256)"
# Target: Must be a valid iron bank market
def test_market_supply(allowlist_registry, allowlist, owner, origin_name, condition_by_id, market):
    # Test valid calldata before adding condition - market.mint(UINT256_MAX)
    data = market.mint.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market, data)
    assert allowed == False

    # Add condition
    condition = condition_by_id("MARKET_SUPPLY")
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - market.mint(UINT256_MAX)
    data = market.mint.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market, data)
    assert allowed == True

# Withdraw

# Description: Market withdraw (cyToken)
# Signature: "market.redeem(uint256)"
# Target: Must be a valid iron bank market
def test_market_redeem_cytoken(allowlist_registry, allowlist, owner, origin_name, condition_by_id, market):
    # Test valid calldata before adding condition - market.redeem(UINT256_MAX)
    data = market.redeem.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market, data)
    assert allowed == False

    # Add condition
    condition = condition_by_id("MARKET_WITHDRAW_CYTOKEN")
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - market.redeem(UINT256_MAX)
    data = market.redeem.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market, data)
    assert allowed == True

# Description: Market withdraw (underlying)
# Signature: "market.redeemUnderlying(uint256)"
# Target: Must be a valid iron bank market
def test_market_redeem_underlying(allowlist_registry, allowlist, owner, origin_name, condition_by_id, market):
    # Test valid calldata before adding condition - market.redeemUnderlying(UINT256_MAX)
    data = market.redeemUnderlying.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market, data)
    assert allowed == False

    # Add condition
    condition = condition_by_id("MARKET_WITHDRAW_UNDERLYING")
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - market.redeemUnderlying(UINT256_MAX)
    data = market.redeemUnderlying.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market, data)
    assert allowed == True

# Borrowing

# Description: Market borrow
# Signature: "market.borrow(uint256)"
# Target: Must be a valid iron bank market
def test_market_borrow(allowlist_registry, allowlist, owner, origin_name, condition_by_id, market):
    # Test valid calldata before adding condition - market.borrow(UINT256_MAX)
    data = market.borrow.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market, data)
    assert allowed == False

    # Add condition
    condition = condition_by_id("MARKET_BORROW")
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - market.borrow(UINT256_MAX)
    data = market.borrow.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market, data)
    assert allowed == True
    
# Repay

# Description: Market repay
# Signature: "market.repayBorrow(uint256)"
# Target: Must be a valid iron bank market
def test_market_repay_borrow(allowlist_registry, allowlist, owner, origin_name, condition_by_id, market):
    # Test valid calldata before adding condition - market.repayBorrow(UINT256_MAX)
    data = market.repayBorrow.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market, data)
    assert allowed == False

    # Add condition
    condition = condition_by_id("MARKET_REPAY")
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - market.repayBorrow(UINT256_MAX)
    data = market.repayBorrow.encode_input(MAX_UINT256)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, market, data)
    assert allowed == True

##############################################################
# Target: Comptroller
##############################################################

# Enter and exit market

# Description: Enter markets
# Signature: "comptroller.enterMarkets(address[])"
# Target: Must be a valid comptroller
# Param0: Must be a valid list of markets
def test_enter_markets(allowlist_registry, allowlist, owner, origin_name, condition_by_id, comptroller_implementation, comptroller_proxy, market):
    # Test valid calldata before adding condition - comptroller.enterMarkets(address[])
    data = comptroller_implementation.enterMarkets.encode_input([market])
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, comptroller_proxy, data)
    assert allowed == False

    # Add condition
    condition = condition_by_id("COMPTROLLER_ENTER_MARKETS")
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - comptroller.enterMarkets(address[])
    data = comptroller_implementation.enterMarkets.encode_input([market])
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, comptroller_proxy, data)
    assert allowed == True
    
# Description: Exit markets
# Signature: "comptroller.exitMarket(address)"
# Target: Must be a valid comptroller
def test_exit_markets(allowlist_registry, allowlist, owner, origin_name, condition_by_id, comptroller_proxy, comptroller_implementation, market):
    # Test valid calldata before adding condition - comptroller.exitMarket(address)
    data = comptroller_implementation.exitMarket.encode_input(market)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, comptroller_proxy, data)
    assert allowed == False

    # Add condition
    condition = condition_by_id("COMPTROLLER_EXIT_MARKET")
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - comptroller.exitMarket(address)
    data = comptroller_implementation.exitMarket.encode_input(market)
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, comptroller_proxy, data)
    assert allowed == True

def test_conditions_json(allowlist):
    all_conditions_json = allowlist.conditionsJson()
    assert(len(all_conditions_json) > 0)

    #####################################################################################
    # Notice: You can print the entire JSON for this test if you uncomment the line below
    #####################################################################################
    # print(all_conditions_json)
