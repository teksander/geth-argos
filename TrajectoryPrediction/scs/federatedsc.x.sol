// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FederatedLearning {
    uint8 constant numParticipants = ${MAXWORKERS};
    uint8 constant minParticipant = numParticipants/2;
    uint16 constant numWeights = 2848;
    int48[numWeights] currentWeights;
    int48[numWeights] nextWeights;
    int16 totalSamples;
    uint8 public currentParticipants;
    uint8 public version; 
    int[minParticipant] rankWeights;
    
    function submitWeights(int16 nbSamples, int48[numWeights] calldata weights) external {
        require(nbSamples>0, "Number of samples trained on must be greater than 0.");
        currentParticipants ++;
        totalSamples += nbSamples;
        if (1 < currentParticipants && currentParticipants < minParticipant){
            for (uint16 i = 0; i < numWeights; i++) nextWeights[i] += weights[i]*nbSamples;
        }else if (currentParticipants == minParticipant) {
            for (uint16 i = 0; i < numWeights; i++) currentWeights[i] = (nextWeights[i] + weights[i]*nbSamples)/totalSamples;
            version ++;
            currentParticipants = 0;
            totalSamples = 0;
        }else{
            for (uint16 i = 0; i < numWeights; i++) nextWeights[i] = weights[i]*nbSamples;
        }
    }

    /*
    * Sets the initial weights, the rankweights and set the version to 1.
    * Can only be called in the beginning of the experiment.
    */
    function setInitWeights(int48[numWeights] memory weights, int[minParticipant] memory rankweights) external{
        require(version == 0, "The weights have already been initialised.");
        currentWeights = weights;
        rankWeights = rankweights;
        version++;
    }

    function getWeights() external view returns(int48[numWeights] memory){
        return currentWeights;
    }

    // returns the address of the client making the call.
    function getAddress() external view returns (address) {
        return msg.sender;
    }
}