// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract MarketForaging {

  mapping(address => uint) public lastPayment;

  uint min_wait = 3;

  function sellResource(uint utility) public {
    if (block.number - lastPayment[msg.sender] > min_wait){
      payable(msg.sender).transfer(utility * 1 ether);
      lastPayment[msg.sender] = block.number;
    }
    
  }
}


