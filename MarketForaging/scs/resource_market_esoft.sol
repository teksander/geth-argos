// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract MarketForaging {

  uint constant epsilon = 50; 
  uint constant expma   = 15; 
  uint constant explore = 0;

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

    // Assignment
    uint meanQ;
    uint count;
    uint worker_count;
  } 

  patch[] private patches;

  uint id_nonce;
  mapping(address => uint) tasks;
  mapping(address => uint) drops;
  mapping(address => uint) lastD;


  function updateMean(uint previous, uint current, uint N) private pure returns (uint) {
    return (previous + expma*current) / (N+expma);
  }

  function random(uint mod) public view returns (uint) {
    return uint(keccak256(abi.encode(block.timestamp,msg.sender))) % mod;
  }

  function coinFlip(uint odds) public view returns (bool) {
    if (random(100) < odds) {
      return true;
    }
    return false;
  }

  function updatePatch(int _x, int _y, uint _qtty, uint _util, string memory _qlty, string memory _json) public {
    
    uint i = findByPos(_x, _y);

    // If patch is already known
    if (i < 9999) { 
      patches[i].qtty  = _qtty;
      patches[i].util  = _util;
      patches[i].qlty  = _qlty;
      patches[i].json  = _json;
    }

    // If patch is new
    else {

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
                          meanQ:   0,
                          count:   0,
                          worker_count: 0
                        }));
    }
  } 

  function dropResource(int _x, int _y, uint _qtty, uint _util, string memory _qlty, string memory _json) public {

    uint i = findByPos(_x, _y);

    if (i < 9999) {

      // Update quality
      uint newQ = 1000*patches[i].util/(block.number-lastD[msg.sender]);

      // patches[i].meanQ = updateMean(patches[i].meanQ, new_value, patches[i].count);
      patches[i].meanQ = newQ;
      patches[i].count ++;
    
      // Update patch information
      updatePatch(_x, _y, _qtty, _util, _qlty, _json);
    }

    // Update robot drop counter;
    drops[msg.sender] ++;
    lastD[msg.sender] = block.number;

    // Re-assign robot
    if (drops[msg.sender] % 1 == 0)  {
      
      // Unassign current task
      tasks[msg.sender] = 0;
      if (i < 9999) { patches[i].worker_count--; }

      // Assign new task
      assignPatch();
    }
  }

  function assignPatch() public {

    uint i = 0;
    
    // Epsilon-soft algorithm
    bool exploit = coinFlip(100-epsilon);
    
    // Soft-greedy policy
    if (exploit) {
      // Get soft-greedy action
      i = findWeightedChoice();
    }

    // Non-greedy policy
    else {
      // Get random action
      i = random(patches.length + explore);
    }

    // Assign new foraging task
    if (i < patches.length) {
      tasks[msg.sender] = patches[i].id;
      lastD[msg.sender] = block.number;
      patches[i].worker_count++;
    }  

  }

  function findWeightedChoice() private view returns (uint) {
    uint sumQ  = 0;
    uint index = 0;

    for (uint i=0; i < patches.length; i++) {
      sumQ += patches[i].meanQ;
    }

    if (sumQ == 0) {
      return random(patches.length + explore);
    }

    uint rand = random(sumQ);
    for (uint i=0; i < patches.length; i++) {
      if (rand < patches[i].meanQ) {
        index = i;
        break;
      }
      rand -= patches[i].meanQ;
    }
    return index;
  }

  function findBestQ() private view returns (uint) {
    uint maxQ  = 0;
    uint index = 0;

    for (uint i=0; i < patches.length; i++) {
      if (patches[i].meanQ + patches[i].util > maxQ) {
        maxQ  = patches[i].meanQ;
        index = i;
      }
    }
    return index;
  }

  function findByID(uint id) private view returns (uint) {

    for (uint i=0; i < patches.length; i++) {
      if (patches[i].id == id) return i;
    }

    return 9999;
  }

  function findByPos(int _x, int _y) private view returns (uint) {
    for (uint i=0; i < patches.length; i++) {
      if (_x == patches[i].x && _y == patches[i].y) {
        return i;
      }
    } 
    return 9999;
  }
  
  function getPatches() public view returns (patch[] memory){
    return patches;
  }

  function getMyPatch() public view returns (string memory){

    uint task_id = tasks[msg.sender];

    if (task_id == 0) return "";

    for (uint i=0; i < patches.length; i++) {
      if (patches[i].id == task_id) return patches[i].json;
    }   

  }  
}