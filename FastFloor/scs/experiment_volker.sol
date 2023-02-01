// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract MarketForaging {

    // These values here meaningless! The actual important values are
    // set below and usually start with "my," e.g., "myBlocksUBI."
   
  int  public mean = 0; // meaningless!
  int  public threshold = 0; // meaningless!
  uint public ticketPrice = 0;
  int  public tau = 0;
  bool public consensusReached = false;
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
  uint[15] blocksUBI = [0,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384];
  int256 W_n;
  address [] public robotsToPay;

  // Currently, the following values are used:
  // uint myValueUBI = 20;
  // uint myTicketPrice = 40;
  // int myThreshold = 2000000;
  // int myTau = 20000;  
 
  struct voteInfo {
      address robotAddress;
      int256 vote;
    }
 
  struct robotInfo {
      address robotAddress;
      bool isRegistered;
      uint payout;
      uint lastUBI;
      uint myVoteCounter;
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
 
  function getBalance() public view returns (uint) {
    return msg.sender.balance;
  }
  function isConverged() public view returns (bool) {
    return consensusReached;
  }
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

  function getMyVotes() public view returns (uint) {
    return robot[msg.sender].myVoteCounter;
  } 

  function registerRobot() public {

    publicLength = blocksUBI.length;  
    //mean = 5000000;
    ticketPrice = 40;

    if (!robot[msg.sender].isRegistered) {
        robot[msg.sender].robotAddress = msg.sender;
        robot[msg.sender].isRegistered = true;
        robotCount += 1;
    }

  }  

  function askForUBI() public returns (uint) {
    // require(robot[msg.sender].isRegistered, "Robot must register first");
    if (!robot[msg.sender].isRegistered) {
    	return 200;
    }
    uint16[15] memory myBlocksUBI = [0,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384];

    // Update the UBI due
    uint payoutUBI;
    uint myValueUBI = 20;

    for (uint i = 0; i < myBlocksUBI.length; i++) {
      if (block.number < myBlocksUBI[i]) {
        payoutUBI = (i - robot[msg.sender].lastUBI) * myValueUBI;
        robot[msg.sender].lastUBI = i;
        break;
      }
    }

    // Transfer the UBI
    if (payoutUBI > 0) {
      payable(msg.sender).transfer(payoutUBI * 1 ether);
    }
    return payoutUBI;
  }



  function askForPayout() public returns (uint) {
    // require(robot[msg.sender].isRegistered, "Robot must register first");

    if (!robot[msg.sender].isRegistered) {
    	return 200;
    }

    // if (!robot[msg.sender].isRegistered) {
    //    return 0;
    // }

    // Update the payout due
    uint payout = robot[msg.sender].payout;

    // Transfer the payout due
    payable(msg.sender).transfer(payout * 1 gwei);
    robot[msg.sender].payout = 0;
    return payout;
  }    
 
  function sendVote(int estimate) public payable {

    require(msg.value >= 39 ether, "Robot must pay the ticket price");
       
    voteCount += 1;

    round[roundCount].push(voteInfo(msg.sender, estimate));
     
    if (round[roundCount].length == robotCount && robotCount > 4) {
      roundCount += 1;
      newRound = true;
    }

    robot[msg.sender].myVoteCounter += 1;
  }
   
  function updateMean() public {  

    require(robot[msg.sender].isRegistered, "Robot must register first");

    require(lastUpdate < roundCount, "Mean has been updated already");

    int oldMean = mean;  
    uint r = lastUpdate;
    int myThreshold = 1000000;
    uint roundVoteOkCount = 0;

    // Check for OK Votes
    for (uint i = 0; i < round[r].length ; i++) {

      int256 delta = round[r][i].vote - mean;

      if (r == 0 || abs(delta) < myThreshold) {
        voteOkCount += 1;
        roundVoteOkCount += 1;

        // Update mean
        int256 w_n = 1;
        W_n = W_n + w_n;
        mean += (w_n * delta) / W_n;

        // Record robots that will be refunded
        robotsToPay.push(round[r][i].robotAddress);
      }
    }

    // If none of the votes fulfills the criteria, accept all votes
    // (this prevents deadlock situations)!
    if (roundVoteOkCount == 0) {
      for (uint i = 0; i < round[r].length ; i++) {

        int256 delta = round[r][i].vote - mean;

        voteOkCount += 1;
        roundVoteOkCount += 1;

        // Update mean
        int256 w_n = 1;
        W_n = W_n + w_n;
        mean += (w_n * delta) / W_n;

        // Record robots that will be refunded
        robotsToPay.push(round[r][i].robotAddress);
      }
    }

    // Compute payouts
    for (uint b = 0; b < robotsToPay.length; b++) {
    robot[robotsToPay[b]].payout += 1 gwei * ticketPrice * round[r].length / robotsToPay.length;
    }

    // Determine consensus
    int myTau = 20000;

    if ((abs(oldMean - mean) < myTau) && voteOkCount > 2 * robotCount) {
      consensusReached = true;
    }

    lastUpdate += 1;
    newRound = false;
    delete robotsToPay;
  }
}
