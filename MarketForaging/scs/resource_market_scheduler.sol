// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract MarketForaging {

  uint constant DCURVE = DCURVE; 
  uint constant epoch  = EPOCH;

  struct patch {

    // Details 
    int x;
    int y;
    uint qtty;
    int[3] demand;  
    string qlty;
    string json; 

    // Identifier
    uint id;

  } 

  address[] queue;
  patch[] private patches;
  
  uint id_nonce;
  mapping(address => uint) tasks;
  mapping(address => uint) drops;


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
                          id:     id_nonce,
                          worker: address(0),
                          lastA: 0,
                          lastD: 0
                        }));
    }
  } 

  function dropResource(int _x, int _y, uint _qtty, uint _util, string memory _qlty, string memory _json) public {

    uint i = findByPos(_x, _y);

    if (i < 9999) {
  
      // Update patch information
      updatePatch(_x, _y, _qtty, _util, _qlty, _json);
    }

    // Update robot drop counter;
    drops[msg.sender] ++;
    patches[i].lastD == block.number;


    // Re-assign robot
    if (drops[msg.sender] % 1 == 0)  {
      
      // Unassign current task
      tasks[msg.sender] = 0;
      if (i < 9999) { patches[i].worker == address(0); }

      // Assign new worker
      assignPatch();
    }
  }

  function joinQueue() public {
    uint t = amInQueue();
    if (t==9999) { queue.push(msg.sender); }
  }


  function assignPatch() public {

    uint i = findBestAvailiable();

    if (i < 9999 && queue.length > 0) {
      address next = queue[0];
      patches[i].worker = next;
      tasks[next] = patches[i].id;

      for (uint j = 0; j < queue.length-1; j++) { queue[j] = queue[j+1]; }
      queue.pop();
    }
  }

  function findBestAvailiable() public view returns (uint) {
    uint maxU  = 0;
    uint index = 9999;

    for (uint i=0; i < patches.length; i++) {
      if (patches[i].worker == address(0) && patches[i].util > maxU) {
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

  function findByPos(int _x, int _y) private view returns (uint) {
    for (uint i=0; i < patches.length; i++) {
      if (_x == patches[i].x && _y == patches[i].y) {
        return i;
      }
    } 
    return 9999;
  }

  function amInQueue() public view returns (uint) {
    for (uint i=0; i < queue.length; i++) {
      if (queue[i] == msg.sender) {
        return i;
      }
    } 
    return 9999;
  }
  
  function getPatches() public view returns (patch[] memory){
    return patches;
  }

  function getQueue() public view returns (address[] memory){
    return queue;
  }


  function getMyPatch() public view returns (string memory){

    uint task_id = tasks[msg.sender];

    if (task_id == 0) return "";

    for (uint i=0; i < patches.length; i++) {
      if (patches[i].id == task_id) return patches[i].json;
    }   

  }  
}