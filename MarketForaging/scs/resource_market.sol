// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract MarketForaging {

  uint constant max_workers = 2;
  uint constant max_stakers = 10;

  uint constant worker_share = 70;
  uint constant staker_share = 30;
  

  // uint constant max_workers = 2;
  // uint constant max_stakers = 5;

  // uint constant worker_share = 70;
  // uint constant staker_share = 30;


  struct resource {
    address scout;
    address[max_workers] workers;
    address[max_stakers] stakers;
    uint[max_stakers] stakes;
    uint stake;
    uint block;

    int x;
    int y;
    uint qtty;
    uint util;
    string qlty;
    string json;
  }   
 
  resource[] public resources;
  resource[] public resources_depleted;

  address[max_workers] public workers_empty;
  address[max_stakers] public stakers_empty;
  uint[max_stakers] public stakes_empty;

  mapping(address => uint) public balances;


  function updatePatch(int _x, int _y, uint _qtty, uint _util, string memory _qlty, string memory _json, uint my_stake) public {
    
    // If patch is not unique
    bool unique = true;
    for (uint i=0; i < resources.length; i++) {
      if (_x == resources[i].x && _y == resources[i].y ) {
        unique = false;

        if (_qtty <= resources[i].qtty) {

          uint reward = (resources[i].qtty - _qtty) * resources[i].util * 100;
          uint worker_reward = reward * worker_share / 100;
          uint staker_reward = reward * staker_share / 100;

          // Reward the stakers
          uint staker_count = 0;
          for (uint j=0; j < max_stakers; j++) { 
            if (resources[i].stakers[j] != address(0)){
              staker_count += 1;
            }
          }

          for (uint j=0; j < staker_count; j++) { 
            balances[resources[i].stakers[j]] += staker_reward * (resources[i].stakes[j] / resources[i].stake);
          }

          // Reward the workers
          uint worker_count = 0;
          for (uint j=0; j < max_workers; j++) { 
            if (resources[i].workers[j] != address(0)){
              worker_count += 1;
            }
          }
        
          for (uint j=0; j < worker_count; j++) { 
            balances[resources[i].workers[j]] += worker_reward / worker_count;
          }

          // Update patch information
          resources[i].block    = block.number;
          resources[i].qtty     = _qtty;
          resources[i].json     = _json;

          // Update the stake
          uint jj = findStakerSpot(i, msg.sender);
          
          if (jj < 999  && my_stake < balances[msg.sender]) {
            resources[i].stakers[jj] = msg.sender;
            resources[i].stakes[jj]  = my_stake * 100;
            resources[i].stake      += my_stake * 100;
            balances[msg.sender] -= my_stake * 100;
          }

        }

        // If resource quantity is 0
        if (resources[i].qtty < 1) {

          // Store in depleted patch array
          resources_depleted.push(resources[i]);

          // Refund all stakers
          for (uint j=0; j < max_stakers; j++) { 
            if (resources[i].stakers[j] != address(0)) {
              balances[resources[i].stakers[j]] += resources[i].stakes[j];
              resources[i].stakes[j] = 0;  
            }
          }
          // Remove depleted patch
          resources[i] = resources[resources.length - 1];
          resources.pop();
        }
        break;
      }
    } 

    // Is patch depleted
    bool depleted = false;
    for (uint i=0; i < resources_depleted.length; i++) {
      if (_x == resources_depleted[i].x && _y == resources_depleted[i].y ) {
        depleted = true;  
      }
    }

    // If patch is unique
    if (unique && !depleted) {

      // Append the new resource to the lists
      resources.push(resource({
                                scout: msg.sender,
                                workers: workers_empty,
                                stakers: stakers_empty,
                                stakes:  stakes_empty,
                                stake:   0,
                                block: block.number,
                                x: _x, 
                                y: _y, 
                                qtty: _qtty, 
                                util: _util,
                                qlty: _qlty, 
                                json: _json
                              }));

      // Update the stake
      if (my_stake < balances[msg.sender]) {
        resources[resources.length - 1].stakers[0]   = msg.sender;
        resources[resources.length - 1].stakes[0]   += my_stake * 100;
        resources[resources.length - 1].stake += my_stake * 100;
        balances[msg.sender] -= my_stake * 100;
      }
    }
  }

  function findStakerSpot(uint resource_index, address staker) internal view returns (uint) {

    for (uint j=0; j < max_stakers; j++) { 
      if (resources[resource_index].stakers[j] == staker) {
        return j;      
      }
    }

    for (uint j=0; j < max_stakers; j++) { 
      if (resources[resource_index].stakers[j] == address(0)) {
        return j;      
      }
    }

    return 1000;
  }

  function findWorker(uint resource_index, address worker) internal view returns (uint) {

    for (uint j=0; j < max_workers; j++) { 
      if (resources[resource_index].workers[j] == worker) {
        return j;      
      }
    }
    return 1000;
  }


  function assignPatch() public {

    // Buy resource with maximum util * reliability
    uint res_index = 0;
    uint rec_index = 0;
    uint max_util = 0;
  
    bool is_recruit = false;
    uint my_res_index = 0;
    uint my_rec_index = 0;

    for (uint i=0; i < resources.length; i++) {
      for (uint j=0; j < max_workers; j++) {

        if (resources[i].workers[j] == msg.sender) {
          is_recruit = true;
          my_res_index = i;
          my_rec_index = j;
        } 
        
        if (resources[i].workers[j] == address(0) && resources[i].util > max_util) {
          max_util = resources[i].util;
          res_index = i;
          rec_index = j;
        }

      }    
    }

    require(max_util > 0, "No resources for sale");

    if (is_recruit && resources[my_res_index].util < max_util) {
      resources[my_res_index].workers[my_rec_index] = address(0);
      is_recruit = false;
    }

    // Update resource recruit
    if (!is_recruit) {
      resources[res_index].workers[rec_index] = msg.sender;
    }
  }

  function getResources() public view returns (resource[] memory){
    return resources;
  }

  function getMyResource() public view returns (string memory){

    for (uint i=0; i < resources.length; i++) {

      for (uint j=0; j < max_workers; j++) {

        if (resources[i].workers[j] == msg.sender) { 
           return resources[i].json; 
        }
      }
    }
    return "";    
  }

  function registerRobot() public {
    balances[msg.sender] = 1000;
  } 
}

