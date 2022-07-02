// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract MarketForaging {

  uint constant epsilon = 70; 

    struct patch {

    // Details 
    int x;
    int y;
    uint qtty;
    uint util;
    string qlty;
    string json; 

    // Identifier
    uint id;

    // Production
    uint lastT;
    uint meanQ;
    uint count;
  } 

  uint id_nonce;
  mapping(address => uint) tasks;

  patch[] private patches;
  patch[] private patches_depleted;
  
  function updateMean(uint previous, uint current, uint N) private pure returns (uint) {
    return (previous*N + current) / (N+1);
  }

  function random(uint mod) private view returns (uint) {
    return uint(keccak256(abi.encode(block.timestamp))) % mod;
  }

  function coinFlip(uint odds) private view returns (bool) {
    if (random(100) < odds) {
      return true;
    }
    return false;
  }

  function registerRobot() public {
    // Register as scout initially
    tasks[msg.sender] = 0;
  }

  function updatePatch(int _x, int _y, uint _qtty, uint _util, string memory _qlty, string memory _json) public {
    bool unique = true;
    bool depleted = false;

    // If patch is not unique
    for (uint i=0; i < patches.length; i++) {
      if (_x == patches[i].x && _y == patches[i].y ) {
        unique = false;

        // Update average quality
        patches[i].meanQ  = updateMean(patches[i].meanQ, patches[i].util/(block.number-patches[i].lastT), patches[i].count);
        patches[i].lastT  = block.number;
        patches[i].count += 1;
      
        patches[i].json   = _json;
        patches[i].qtty   = _qtty;

        // Remove patch if quantity is 0
        if (patches[i].qtty < 1) {
          patches_depleted.push(patches[i]);
          patches[i] = patches[patches.length - 1];
          patches.pop();
        }
        break;
      }
    } 

    // Is patch depleted
    for (uint i=0; i < patches_depleted.length; i++) {
      if (_x == patches_depleted[i].x && _y == patches_depleted[i].y ) {
        depleted = true;
        break;
      }
    }

    // If patch is unique
    if (unique && !depleted) { 

      // Increment unique patch id
      id_nonce++;

      // Append new patch to list
      patches.push(patch({
                          x: _x, 
                          y: _y, 
                          qtty: _qtty, 
                          util: _util,
                          qlty: _qlty, 
                          json: _json,
                          id:      id_nonce,
                          lastT:   block.number,
                          meanQ:   0,
                          count:   0
                        }));


    }
  } 

  function findBest() private view returns (uint) {
    uint maxQ  = 0;
    uint index = 0;

    for (uint i=0; i < patches.length; i++) {
      if (patches[i].meanQ > maxQ) {
          index = i;
        } 
    }
    return index;
  }

  function assignPatch() public {

    // Epsilon-greedy algorithm
    bool exploit = coinFlip(100-epsilon);

    // Greedy policy
    if (exploit) {
      // Get maximum quality patch
      (uint i) = findBest();

      // Assign worker
      tasks[msg.sender] = patches[i].id;
    }

    // Non-greedy policy
    else {
      // Get random action
      uint i = random(patches.length+1);

      // Assign worker
      if (i < patches.length) {
        tasks[msg.sender] = patches[i].id;
      }  

      // Assign scout
      else {
        tasks[msg.sender] = 0;
      }
    }
  }

  function getPatches() public view returns (patch[] memory){
    return patches;
  }

  function getMyPatch() public view returns (string memory){

    uint task_id = tasks[msg.sender];

    if (task_id == 0) return "";

    for (uint i=0; i < patches.length; i++) {
      if (patches[i].id == task_id) {
          return patches[i].json;
      } 
    }   
  }  
}


