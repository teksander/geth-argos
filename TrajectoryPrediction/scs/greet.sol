// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract HelloNeighbor {
    string public greeting;
    uint public greetingCount;


    // function append(memory string a, memory string b) internal pure returns (memory string) {
    // return string(abi.encodePacked(a, b));
    
    function setGreeting() public {
        greeting = "Hello neighbor";
    }

    function greet() public {
        greetingCount += 1;
    }


    // uint public helloCount;

    // struct helloInfo {
    //   address payable neighborAddress;
    //   uint message;
    // }

    // helloInfo[] helloList;

    // function Greeters() public {
    //     greeting = 0;
    // }

    // function setGreeting(uint _greeting) public {
    //     greeting += _greeting;
    //     voteInfo memory vi = voteInfo(msg.sender, _greeting);
    //     voteList.push(vi);
    //     if (voteList.length == 4) {
    //          greeting = 0;
    //     }
    // }

    // function greet() view public returns (uint) {
    // return greeting;
    // }
}
