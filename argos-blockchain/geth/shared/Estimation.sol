// SPDX-License-Identifier: MIT
pragma solidity ^0.7.0;
contract Estimation {

  int  public mean = 5000000;
  int  public threshold = 2000000;
  uint public ticketPrice = 40;
  int  public tau = 100000;
  uint public consensusReached = 1;
  uint public startBlock = 0;
  uint public valueUBI = 20;
  uint public publicPayoutUBI = 0;
  uint public publicLength = 0;	
  uint public roundCount = 0;
  uint public voteCount = 0;
  uint public voteOkCount = 0;
  uint public robotCount = 0;
  uint public lastUpdate = 0;
  bool public newRound = false;
  uint[10] blocksUBI = [0,2,4,8,16,32,64,128,256,512]; 
  int256 W_n;
  address payable [] public robotsToPay;

  struct voteInfo {
      address payable robotAddress;
      int256 vote;
    }
  
  struct robotInfo {
      address payable robotAddress;
      bool isRegistered;
      uint payout;
      uint lastUBI;
    }
   
  mapping(address => robotInfo) public robot;
  mapping(uint => voteInfo[]) public round;

  function abs(int x) internal pure returns (int y) {
    if (x < 0) {
      return -x;
    } 
    else {
      return x;
    }
  }
  
  function sqrt(int x) internal pure returns (int y) {
    int z = (x + 1) / 2;
    y = x;
    while (z < y) {
      y = z;
      z = (x / z + z) / 2;
    }
  }

  function UBIlength() public view returns (uint) {
    return blocksUBI.length;
  }

//  function isConverged() public view returns (bool) {
//    return consensusReached;
//  }
  function isNewRound() public view returns (bool) {
    return newRound;
  }
  function getMean() public view returns (int) {
    return mean;
  }
  function getVoteCount() public view returns (uint) {
    return voteCount;
  }
  function getVoteOkCount() public view returns (uint) {
    return voteOkCount;
  }
  function getRobotCount() public view returns (uint) { 
    return robotCount;
  }
  function getTicketPrice() public view returns (uint) { 
    return ticketPrice;
  }
  function sendFund() public payable {
  }

  function registerRobot() public {

    publicLength = blocksUBI.length;	   
    mean = 5000000;
    ticketPrice = 40;

    if (!robot[msg.sender].isRegistered) {
        robot[msg.sender].robotAddress = msg.sender;
        robot[msg.sender].isRegistered = true;
        robotCount += 1;
    }

  }
  

  function askForUBI() public returns (uint) {
    if (!robot[msg.sender].isRegistered) {
       return 0;
    }

    uint16[10] memory myBlocksUBI = [0,2,4,8,16,32,64,128,256,512];

    // Update the UBI due
    uint payoutUBI;
    uint myValueUBI = 20;

    for (uint i = 0; i < myBlocksUBI.length; i++) {
      if (block.number-startBlock < myBlocksUBI[i]) {
      payoutUBI = (i - robot[msg.sender].lastUBI) * myValueUBI;
      robot[msg.sender].lastUBI = i;
      break;
      }
    }

    // Transfer the UBI due
    if (payoutUBI > 0) {
      msg.sender.transfer(payoutUBI * 1 ether);
    }
    return payoutUBI;
  }

  function askForPayout() public returns (uint) {
    if (!robot[msg.sender].isRegistered) {
       return 0;
    }

    // Update the payout due
    uint payout = robot[msg.sender].payout;

    // Transfer the payout due
    msg.sender.transfer(payout * 1 ether);
    robot[msg.sender].payout = 0;
    return payout;
  }    
  
  function sendVote(int estimate) public payable {

  uint myTicketPrice = 40;	  

    if (!robot[msg.sender].isRegistered || msg.value < myTicketPrice * 1 ether) {
       revert();
    }
    
    voteCount += 1;

    round[roundCount].push(voteInfo(msg.sender, estimate));
    
    if (round[roundCount].length == robotCount) {
      roundCount += 1;
      newRound = true;
    }
  }
    
  function updateMean() public {  
    if (!robot[msg.sender].isRegistered || lastUpdate >= roundCount) {
       revert();
    }

    int oldMean = mean;  
    uint r = lastUpdate;
    int myThreshold = 2000000;	

    // Check for OK Votes
    for (uint i = 0; i < round[r].length ; i++) {

      int256 delta = round[r][i].vote - mean;
  
      if (r == 0 || abs(delta) < myThreshold) {
        voteOkCount += 1;

        // Update mean
        int256 w_n = 1;
        W_n = W_n + w_n;
        mean += (w_n * delta) / W_n;

        // Record robots to be refunded
        robotsToPay.push(round[r][i].robotAddress);
      } 
    } 

    // Compute payouts
    for (uint b = 0; b < robotsToPay.length; b++) {
    robot[robotsToPay[b]].payout += ticketPrice * (round[r].length / robotsToPay.length);
    }

    // Determine consensus
    int myTau = 100000;	

    if ((abs(oldMean - mean) < myTau) && voteOkCount > 2*robotCount) {
      consensusReached = 2;
    }

    lastUpdate += 1;
    newRound = false;
    delete robotsToPay;
  }
}
