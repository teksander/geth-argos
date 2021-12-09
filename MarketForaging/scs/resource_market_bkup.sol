// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract MarketForaging {

  struct resource {
    address explorer;
    address recruit;
    uint id;
    string json;
    int x;
    int y;
    uint qtty;
    string qlty;
    int value;
    uint price;
    uint decrease_rate;
    uint block;
  }   
 
 resource[] public resource_list;
 mapping(address => string) public purchases;
 uint public id = 0;

function addResource(string memory _json, int _x, int _y, uint _qtty, string memory _qlty, int _value, uint _price, uint _decrease_rate) public {

  for (uint i=0; i < resource_list.length; i++) {
    if (keccak256(bytes(_json)) == keccak256(bytes(resource_list[i].json))) {
      return;
    }
  }

  resource_list.push(resource(msg.sender, address(0), id, _json, _x, _y, _qtty, _qlty,_value, _price, _decrease_rate, block.number));
  id += 1;
} 


function getResources() public view returns (resource[] memory){
  return resource_list;
}

function buyFuel() public payable {}


function buyResource() public payable{
  uint min_price = 999999;
  uint min_index = 0;
  string memory min_json;

  require(resource_list.length > 0, "No resources availiable");

  for (uint i=0; i < resource_list.length; i++) {
    if (resource_list[i].price < min_price && resource_list[i].recruit == address(0)) {
      min_index = i;
      min_price = resource_list[i].price;
      min_json = resource_list[i].json;
      break;
    }
  }

  require(msg.value >= min_price * 1 ether, "Pay minimum value");

  // Inform buyer of purchase
  purchases[msg.sender] = min_json;


  // Pay to the explorer of the resource
  payable(resource_list[min_index].explorer).transfer(min_price * 1 ether);

  // Refund the buyer for the difference
  payable(msg.sender).transfer(msg.value - min_price * 1 ether);

  // // Store the resource buyer
  // resource_list[min_index].recruit = msg.sender;

  // Remove the purchased resource
  resource_list[min_index] = resource_list[resource_list.length - 1];
  resource_list.pop();


}

function sellItem(uint _value) public {

  payable(msg.sender).transfer(_value * 1 ether);

}

// function sellItem(uint _id) public payable {

//   for (uint i=0; i < resource_list.length; i++) {

//     if (resource_list[i].id == _id && resource_list[i].recruit == msg.sender) {
//       min_price = resource_l==st[i].price;
//       min_index = i;
//       break;
//     }

//   }

// }

function removeResource() public {

    }

  // // We overwrite the sold resource with the last element in list
  // resource_list[min_index] = resource_list[resource_list.length - 1];

  // // We delete the last element in list
  // resource_list.pop();


// function buyResource() public payable {
//   uint index;
//   bool found;

//   for (uint i=0; i < resource_list.length; i++) {
//     found = false;
//     if (resource_list[i].id == _id) {
//       index = i;
//       found = true;
//       break;
//     }

//   }

//   require(found, "Resource not found");

//   require(msg.value >= resource_list[index].price * 1 ether, "Pay the correct value");

//   payable(resource_list[index].explorer).transfer(msg.value);


//   // // We overwrite the sold resource with the last element in list
//   // resource_list[index] = resource_list[resource_list.length - 1];

//   // // We delete the last element in list
//   // resource_list.pop();


// }





function getAllowance() public {
    uint allowance = 21;

    // Transfer the allowance
    if (msg.sender.balance * 1 ether - allowance * 1 ether < 0) {
      payable(msg.sender).transfer(allowance * 1 ether - msg.sender.balance * 1 ether);
    }

}

// function updatePrices() public {  

//   for (uint i=0; i < resource_list.length; i++) {

//     blocks_elapsed = block.number - resource_list[i].block
//     resource_list[i].block = block.number

//     resource_list[i].price = resource_list[i].price - resource_list[i].decrease_rate * blocks_elapsed
//     }
//   }

   
//   mapping(address => robotInfo) public robot;
//   mapping(uint => voteInfo[]) public round;

//   function abs(int x) internal pure returns (int y) {
//     if (x < 0) {
//       return -x;
//     }
//     else {
//       return x;
//     }
//   }
 
//   function getBalance() public view returns (uint) {
//     return msg.sender.balance;
//   }
//   function isConverged() public view returns (bool) {
//     return consensusReached;
//   }
//   function isNewRound() public view returns (bool) {
//     return newRound;
//   }
//   function getMean() public view returns (int) {
//     return mean;
//   }
//   function getVoteCount() public view returns (uint) {
//     return voteCount;
//   }
//   function getVoteOkCount() public view returns (uint) {
//     return voteOkCount;
//   }
//   function getRobotCount() public view returns (uint) {
//     return robotCount;
//   }
//   function getTicketPrice() public view returns (uint) {
//     return ticketPrice;
//   }


  // function registerRobot() public {

  //   publicLength = blocksUBI.length;  
  //   //mean = 5000000;
  //   ticketPrice = 40;

  //   if (!robot[msg.sender].isRegistered) {
  //       robot[msg.sender].robotAddress = msg.sender;
  //       robot[msg.sender].isRegistered = true;
  //       robotCount += 1;
  //   }

  // }  





 //  function askForUBI() public returns (uint) {
 //    require(robot[msg.sender].isRegistered, "Robot must register first");

 //    uint16[10] memory myBlocksUBI = [0,2,4,8,16,32,64,128,256,512];

 //    // Update the UBI due
 //    uint payoutUBI;
 //    uint myValueUBI = 20;

 //    for (uint i = 0; i < myBlocksUBI.length; i++) {
 //      if (block.number < myBlocksUBI[i]) {
 // payoutUBI = (i - robot[msg.sender].lastUBI) * myValueUBI;
 // robot[msg.sender].lastUBI = i;
 // break;
 //      }
 //    }

 //    // Transfer the UBI
 //    if (payoutUBI > 0) {
 //      payable(msg.sender).transfer(payoutUBI * 1 ether);
 //    }
 //    return payoutUBI;
 //  }


//   function askForPayout() public returns (uint) {
//     require(robot[msg.sender].isRegistered, "Robot must register first");

//     // if (!robot[msg.sender].isRegistered) {
//     //    return 0;
//     // }

//     // Update the payout due
//     uint payout = robot[msg.sender].payout;

//     // Transfer the payout due
//     payable(msg.sender).transfer(payout * 1 ether);
//     robot[msg.sender].payout = 0;
//     return payout;
//   }    
 
//   function sendVote(int estimate) public payable {

//   // uint myTicketPrice = 39;  

//   //require(robot[msg.sender].isRegistered, "Robot must register first");

//   require(msg.value >= 39 ether, "Robot must pay the ticket price");

//   // uint myTicketPrice = 40;  
//   //   if (!robot[msg.sender].isRegistered || msg.value < myTicketPrice * 1 ether) {
//   //      revert();
//   //   }
   
//   //  if (msg.value > myTicketPrice * 1 ether) {
       
//     voteCount += 1;

//       round[roundCount].push(voteInfo(msg.sender, estimate));
   
//       if (round[roundCount].length == robotCount && robotCount > 4) {
//         roundCount += 1;
//         newRound = true;
//     }

//     robot[msg.sender].myVoteCounter += 1;
//   //}
    
//   }
   
//   function updateMean() public {  

//     require(robot[msg.sender].isRegistered, "Robot must register first");

//     require(lastUpdate < roundCount, "Mean has been updated already");

//     // if (!robot[msg.sender].isRegistered || lastUpdate >= roundCount) {
//     //    revert();
//     // }

//     int oldMean = mean;  
//     uint r = lastUpdate;
//     int myThreshold = 1000000;

//     // Check for OK Votes
//     for (uint i = 0; i < round[r].length ; i++) {

//       int256 delta = round[r][i].vote - mean;

//       if (r == 0 || abs(delta) < myThreshold) {
//         voteOkCount += 1;

//         // Update mean
//         int256 w_n = 1;
//         W_n = W_n + w_n;
//         mean += (w_n * delta) / W_n;

//         // Record robots that will be refunded
//         robotsToPay.push(round[r][i].robotAddress);
//       }
//     }

//     // Compute payouts
//     for (uint b = 0; b < robotsToPay.length; b++) {
//     robot[robotsToPay[b]].payout += ticketPrice * round[r].length / robotsToPay.length;
//     }

//     // Determine consensus
//     int myTau = 20000;

//     if ((abs(oldMean - mean) < myTau) && voteOkCount > 2 * robotCount) {
//       consensusReached = true;
//     }

//     lastUpdate += 1;
//     newRound = false;
//     delete robotsToPay;
//   }
}
