// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

/*******************************************************
 *                      Interfaces
 *******************************************************/
interface IRegistry {
  function isRegistered(address) external view returns (bool);

  function numVaults(address) external view returns (uint256);

  function vaults(address, uint256) external view returns (address);
}

interface IVault {
  function token() external view returns (address);
}

interface IAllowlistFactory {
  function protocolOwnerAddressByOriginName(string memory originName)
    external
    view
    returns (address ownerAddress);
}

/*******************************************************
 *                      Implementation
 *******************************************************/
contract YearnAllowlistImplementation {
  address public registryAddress;
  address public allowlistFactoryAddress;
  string public constant protocolOriginName = "yearn.finance";
  mapping(address => bool) public isZapInContract;
  mapping(address => bool) public isZapOutContract;

  constructor(address _registryAddress, address _allowlistFactoryAddress) {
    registryAddress = _registryAddress;
    allowlistFactoryAddress = _allowlistFactoryAddress;
  }

  function setIsZapInContract(address spenderAddress, bool allowed)
    public
    onlyOwner
  {
    isZapInContract[spenderAddress] = allowed;
  }

  function setIsZapOutContract(address spenderAddress, bool allowed)
    public
    onlyOwner
  {
    isZapOutContract[spenderAddress] = allowed;
  }

  modifier onlyOwner() {
    require(
      msg.sender == ownerAddress() || msg.sender == address(0),
      "Caller is not the protocol owner"
    );
    _;
  }

  function ownerAddress() public view returns (address protcolOwnerAddress) {
    protcolOwnerAddress = IAllowlistFactory(allowlistFactoryAddress)
      .protocolOwnerAddressByOriginName(protocolOriginName);
  }

  /**
   * @notice Determine whether or not a vault address is a valid vault
   * @param tokenAddress The vault token address to test
   * @return Returns true if the valid address is valid and false if not
   */
  function isVaultUnderlyingToken(address tokenAddress)
    public
    view
    returns (bool)
  {
    return registry().isRegistered(tokenAddress);
  }

  /**
   * @notice Determine whether or not a vault address is a valid vault
   * @param vaultAddress The vault address to test
   * @return Returns true if the valid address is valid and false if not
   */
  function isVault(address vaultAddress) public view returns (bool) {
    IVault vault = IVault(vaultAddress);
    address tokenAddress;
    try vault.token() returns (address _tokenAddress) {
      tokenAddress = _tokenAddress;
    } catch {
      return false;
    }
    uint256 numVaults = registry().numVaults(tokenAddress);
    for (uint256 vaultIdx; vaultIdx < numVaults; vaultIdx++) {
      address currentVaultAddress = registry().vaults(tokenAddress, vaultIdx);
      if (currentVaultAddress == vaultAddress) {
        return true;
      }
    }
    return false;
  }

  /**
   * @dev Internal convienence method used to fetch registry interface
   */
  function registry() internal view returns (IRegistry) {
    return IRegistry(registryAddress);
  }
}
