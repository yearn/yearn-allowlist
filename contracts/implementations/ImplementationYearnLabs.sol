// SPDX-License-Identifier: MIT
pragma solidity 0.8.11;

/*******************************************************
 *                      Implementation
 *******************************************************/
contract YearnLabsAllowlistImplementation {
  address public constant pickleJarAddress =
    0xCeD67a187b923F0E5ebcc77C7f2F7da20099e378;
  address pickleGaugeAddress = 0xDA481b277dCe305B97F4091bD66595d57CF31634;
  address yveCrvVaultAddress = 0xc5bDdf9843308380375a611c18B50Fb9341f502A;
  address threeCrvZapAddress = 0x579422A1C774470cA623329C69f27cC3bEB935a1;

  constructor() {
    uint256 chainId;
    assembly {
      chainId := chainid()
    }
  }

  function isPickleJar(address jarAddress) public view returns (bool) {
    return jarAddress == pickleJarAddress;
  }

  function isPickleGauge(address gaugeAddress) public view returns (bool) {
    return gaugeAddress == pickleGaugeAddress;
  }

  function isYveCrvVault(address vaultAddress) public view returns (bool) {
    return vaultAddress == yveCrvVaultAddress;
  }

  function isThreeCrvZap(address zapAddress) public view returns (bool) {
    return zapAddress == threeCrvZapAddress;
  }
}
