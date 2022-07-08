// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract MarketForaging {

  uint constant max_workers = 11; 

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
  patch[] private patches_depleted;

  uint id_nonce;
  mapping(address => uint) tasks;
  mapping(address => uint) drops;
  mapping(address => uint) lastD;


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

  function updatePatch(int _x, int _y, uint _qtty, uint _util, string memory _qlty, string memory _json) public {
    bool unique = true;
    bool depleted = false;

    // Is patch unique
    for (uint i=0; i < patches.length; i++) {
      if (_x == patches[i].x && _y == patches[i].y ) {
        unique = false;

        // Remove patch if quantity is 0
        if (_qtty < 1) {
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
                          meanQ:   0,
                          count:   0,
                          worker_count: 0
                        }));
    }
  } 

  function dropResource(int _x, int _y, uint _qtty, uint _util, string memory _qlty, string memory _json) public {

    for (uint i=0; i < patches.length; i++) {
      if (_x == patches[i].x && _y == patches[i].y ) {

        // Update average quality
        patches[i].meanQ = updateMean(patches[i].meanQ, 1000*patches[i].util/(block.number-lastD[msg.sender]), patches[i].count);
        patches[i].count ++;
      
        patches[i].json  = _json;
        patches[i].qtty  = _qtty;

        // Update robot drop counter;
        drops[msg.sender] ++;
        lastD[msg.sender] = block.number;

        // Re-assign robot
        if (drops[msg.sender] % 1 == 0)  {
          assignPatch();
        }

        // Update patch information
        updatePatch(_x, _y, _qtty, _util, _qlty, _json);

      }
    }
  }

  function assignPatch() public {

    // Limit foragers algorithm
    uint i = findBestAvailiable();
    uint j = findByID(tasks[msg.sender]);

    // Assign if there is availiable
    if (i<9999) {

      tasks[msg.sender] = 0;
      if (j<9999) {
        patches[j].worker_count--;
      }
      
      // Assign new foraging task
      if (i < patches.length) {
        tasks[msg.sender] = patches[i].id;
        lastD[msg.sender] = block.number;
        patches[i].worker_count++;
      }  
    }
  }

  function findBest() private view returns (uint) {
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

  function findBestAvailiable() private view returns (uint) {
    uint maxU  = 0;
    uint index = 9999;

    for (uint i=0; i < patches.length; i++) {
      if (patches[i].util > maxU && patches[i].worker_count < max_workers) {
        maxU  = patches[i].util;
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