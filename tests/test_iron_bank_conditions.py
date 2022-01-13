import pytest
from brownie import Contract, ZERO_ADDRESS, chain
from brownie.convert import to_bytes

MAX_UINT256 = 2**256-1

@pytest.fixture
def implementation(owner, IronBankAllowlistImplementation, address_provider, allowlist_factory):
    return IronBankAllowlistImplementation.deploy(address_provider, allowlist_factory, {"from": owner})

@pytest.fixture
def market(registry_adapter):
    return Contract(registry_adapter.assetsAddresses()[0])

@pytest.fixture
def registry_adapter(address_provider):
    return Contract(address_provider.addressById("REGISTRY_ADAPTER_IRON_BANK"))

@pytest.fixture
def comptroller(registry_adapter):
    return Contract(registry_adapter.comptrollerAddress())

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
def test_token_approval_for_market(allowlist_factory, allowlist, owner, origin_name, implementation, market, market_token):
    # Add condition
    condition = (
        "approve",
        ["address", "uint256"],
        [
            ["target", "isMarketUnderlyingToken"], 
            ["param", "isMarket", "0"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata - token.approve(market, UINT256_MAX)
    data = market_token.approve.encode_input(market, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market_token, data)
    assert allowed == True
    
    # Test invalid param - token.approve(not_market, UINT256_MAX)
    data = market_token.approve.encode_input(ZERO_ADDRESS, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market_token, data)
    assert allowed == False
    
    # Test invalid target - random_contract.approve(market, UINT256_MAX)
    data = market_token.approve.encode_input(market, MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, ZERO_ADDRESS, data)
    assert allowed == False
    
    # Test invalid method - token.decimals()
    data = market_token.decimals.encode_input()
    allowed = allowlist_factory.validateCalldata(origin_name, market_token, data)
    assert allowed == False

##############################################################
# Target: Markets
##############################################################

# Supply

# Description: Market supply
# Signature: "market.mint(uint256)"
# Target: Must be a valid iron bank market
def test_market_supply(allowlist_factory, allowlist, owner, origin_name, implementation, market):
    # Test valid calldata before adding condition - market.mint(UINT256_MAX)
    data = market.mint.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market, data)
    assert allowed == False

    # Add condition
    condition = (
        "mint",
        ["uint256"],
        [
            ["target", "isMarket"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - market.mint(UINT256_MAX)
    data = market.mint.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market, data)
    assert allowed == True

# Withdraw

# Description: Market withdraw (cyToken)
# Signature: "market.redeem(uint256)"
# Target: Must be a valid iron bank market
def test_market_redeem_cytoken(allowlist_factory, allowlist, owner, origin_name, implementation, market):
    # Test valid calldata before adding condition - market.redeem(UINT256_MAX)
    data = market.redeem.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market, data)
    assert allowed == False

    # Add condition
    condition = (
        "redeem",
        ["uint256"],
        [
            ["target", "isMarket"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - market.redeem(UINT256_MAX)
    data = market.redeem.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market, data)
    assert allowed == True

# Description: Market withdraw (underlying)
# Signature: "market.redeemUnderlying(uint256)"
# Target: Must be a valid iron bank market
def test_market_redeem_underlying(allowlist_factory, allowlist, owner, origin_name, implementation, market):
    # Test valid calldata before adding condition - market.redeemUnderlying(UINT256_MAX)
    data = market.redeemUnderlying.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market, data)
    assert allowed == False

    # Add condition
    condition = (
        "redeemUnderlying",
        ["uint256"],
        [
            ["target", "isMarket"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - market.redeemUnderlying(UINT256_MAX)
    data = market.redeemUnderlying.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market, data)
    assert allowed == True

# Borrowing

# Description: Market borrow
# Signature: "market.borrow(uint256)"
# Target: Must be a valid iron bank market
def test_market_borrow(allowlist_factory, allowlist, owner, origin_name, implementation, market):
    # Test valid calldata before adding condition - market.borrow(UINT256_MAX)
    data = market.borrow.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market, data)
    assert allowed == False

    # Add condition
    condition = (
        "borrow",
        ["uint256"],
        [
            ["target", "isMarket"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - market.borrow(UINT256_MAX)
    data = market.borrow.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market, data)
    assert allowed == True
    
# Repay

# Description: Market repay
# Signature: "market.repayBorrow(uint256)"
# Target: Must be a valid iron bank market
def test_market_repay_borrow(allowlist_factory, allowlist, owner, origin_name, implementation, market):
    # Test valid calldata before adding condition - market.repayBorrow(UINT256_MAX)
    data = market.repayBorrow.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market, data)
    assert allowed == False

    # Add condition
    condition = (
        "repayBorrow",
        ["uint256"],
        [
            ["target", "isMarket"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - market.repayBorrow(UINT256_MAX)
    data = market.repayBorrow.encode_input(MAX_UINT256)
    allowed = allowlist_factory.validateCalldata(origin_name, market, data)
    assert allowed == True

##############################################################
# Target: Comptroller
##############################################################

# Enter and exit market

# Description: Enter markets
# Signature: "comptroller.enterMarkets(address[])"
# Target: Must be a valid comptroller
# Param0: Must be a valid list of markets
def test_enter_markets(allowlist_factory, allowlist, owner, origin_name, implementation, comptroller, market):
    # Test valid calldata before adding condition - comptroller.enterMarkets(address[])
    data = comptroller.enterMarkets.encode_input([market])
    allowed = allowlist_factory.validateCalldata(origin_name, comptroller, data)
    assert allowed == False

    # Add condition
    condition = (
        "enterMarkets",
        ["address[]"],
        [
            ["target", "isComptroller"],
            ["param", "areMarkets", "0"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - comptroller.enterMarkets(address[])
    data = comptroller.enterMarkets.encode_input([market])
    allowed = allowlist_factory.validateCalldata(origin_name, comptroller, data)
    assert allowed == True
    
# Description: Exit markets
# Signature: "comptroller.exitMarket(address)"
# Target: Must be a valid comptroller
def test_exit_markets(allowlist_factory, allowlist, owner, origin_name, implementation, comptroller, market):
    # Test valid calldata before adding condition - comptroller.exitMarket(address)
    data = comptroller.exitMarket.encode_input(market)
    allowed = allowlist_factory.validateCalldata(origin_name, comptroller, data)
    assert allowed == False

    # Add condition
    condition = (
        "exitMarket",
        ["address"],
        [
            ["target", "isComptroller"],
            ["param", "isMarket", "0"]
        ],
        implementation
    )
    allowlist.addCondition(condition, {"from": owner})
    
    # Test valid calldata after adding condition - comptroller.exitMarket(address)
    data = comptroller.exitMarket.encode_input(market)
    allowed = allowlist_factory.validateCalldata(origin_name, comptroller, data)
    assert allowed == True