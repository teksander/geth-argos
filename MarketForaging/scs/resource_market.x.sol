// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract MarketForaging {

  uint constant max_recruits     = MAXRECRUITS;
  uint256 constant forager_share = FORAGERSHARE;
  uint256 constant scout_share   = SCOUTSHARE;

    struct resource {
    address scout;
    address[max_recruits] recruits;
    uint counter;
    string json;
    int x;
    int y;
    uint qtty;
    string qlty;
    uint utility;
    uint block;
  }   
 
  resource[] public resources;
  resource[] public resources_depleted;
  address[max_recruits] public recruits_empty;
  mapping(address => uint) public balances;


  function sellResource(uint _utility) public {
    balances[msg.sender] += 100*_utility;
  } 

  function updatePatch(string memory _json, int _x, int _y, uint _qtty, string memory _qlty, uint _utility) public {
    
    // If patch is not unique
    bool unique = true;
    for (uint i=0; i < resources.length; i++) {
      if (_x == resources[i].x && _y == resources[i].y ) {
        unique = false;


        if (_qtty <= resources[i].qtty) {

          uint reward = (resources[i].qtty - _qtty) * resources[i].utility * 100;
          uint forager_reward = reward * forager_share / 100;
          uint scout_reward   = reward * scout_share / 100;

          // Reward the scout
          balances[resources[i].scout] += scout_reward;

          // Reward the foragers
          uint forager_count = 0;
          for (uint j=0; j < max_recruits; j++) { 
            forager_count += 1;
            if (resources[i].recruits[j] == address(0)){
              break;
            }
          }
        
          for (uint j=0; j < max_recruits; j++) { 
            balances[resources[i].recruits[j]] += forager_reward / forager_count;
          }

          // Update patch information
          resources[i].counter += 1;
          resources[i].json     = _json;
          resources[i].qtty     = _qtty;
          resources[i].block    = block.number;
  
        }

        // Remove patch if quantity is 0
        if (resources[i].qtty < 1) {
          resources_depleted.push(resources[i]);
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
        break;
      }
    }

    // If patch is unique
    if (unique && !depleted) {
      // Append the new resource to the list
      resources.push(resource(msg.sender, recruits_empty, 0, _json, _x, _y, _qtty, _qlty, _utility, block.number));
    }

  } 

  function buyResource() public {

    // Buy resource with maximum utility
    uint res_index = 0;
    uint rec_index = 0;
    uint max_utility = 0;
  
    bool is_recruit = false;
    uint my_res_index = 0;
    uint my_rec_index = 0;

    for (uint i=0; i < resources.length; i++) {
      for (uint j=0; j < max_recruits; j++) {

        if (resources[i].recruits[j] == msg.sender) {
          is_recruit = true;
          my_res_index = i;
          my_rec_index = j;
        } 
        
        if (resources[i].recruits[j] == address(0) && resources[i].utility > max_utility) {
          max_utility = resources[i].utility;
          res_index = i;
          rec_index = j;
        }

      }    
    }

    require(max_utility > 0, "No resources for sale");

    if (is_recruit && resources[my_res_index].utility < max_utility) {
      resources[my_res_index].recruits[my_rec_index] = address(0);
      is_recruit = false;
    }

    // Update resource recruit
    if (!is_recruit) {
      resources[res_index].recruits[rec_index] = msg.sender;
    }
  }

  function getResources() public view returns (resource[] memory){
    return resources;
  }

  function getMyResource() public view returns (string memory){

    for (uint i=0; i < resources.length; i++) {

      for (uint j=0; j < max_recruits; j++) {

        if (resources[i].recruits[j] == msg.sender) { 
           return resources[i].json; 
        }
      }
    }
    return "";    
  }
  
}

