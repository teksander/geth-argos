// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FederatedLearning { // working don't touch !
    uint8 constant numParticipants = ${MAXWORKERS}; // number of robots in an experiment
    uint8 constant minParticipant = numParticipants/2; // number of participant required for a round of aggregation
    uint16 constant numWeights = 2848; // number of weights of the neural networks
    int48[numWeights] currentWeights; // the last valid aggregated weights from the previous round
    int48[numWeights] nextWeights; // the nextweights (note : the new weights are continously added to the nextweights to reduce the amount of gas per call)
    address[] participantsList; // the participants of a round of aggregation
    int totalSamplesAccepted; // the sum of the number of samples of the weights that have been accepted for an aggregation round
    int totalSamplesSubmitted; // the sum of the number of samples of all the weights that have been submitted for an aggregation round
    uint8 currentParticipants; // The current number of participants for an aggregation round 
    uint8 public version; // the version (the number of aggregation round that took place) of the currentWeights.
    uint constant aggregationPrice = 5 ether; // the price in wei of an aggregation round (to have in either divide by 10e17) (note : normally 1 ether = 10e18)
    uint constant errorThreshold = 50000000; // threshold value over which weights are not considered valid and won't be used for an aggregation round. max(MAE of good robot) = 10**7

    struct Participant {
        int samples; // the number of samples associated to the wieghts of this participant
        bool participates; // if he is participating in the current round of aggregation
        bool accepted; // if he is accpeted in the current round of aggregation
        uint mae;
    }

    mapping (address => Participant) participantsValue; // mapping from a client address to his personal info.

    

    /*
    * Payable function used externaly to submit ones weights to the blockchain.
    * For the weights to be elligeable, certain criterion must be followed:
    *   The caller must send aggregationPrice when calling the function. (If his weights are valid
    *   the called will be rewarded minimum this amount.)
    *   He must have trained his weights with more than 0.
    *   He musn't participate multiple times for a same aggregation round.
    * Then if all the above conditions are met, the Weights will be tested against an error function.
    * if the error is greater than errorThreshold, then the weights will be discarded and the sender will loose
    * some ethereum. This is to prevent bad behaving agents.
    * After all this the weights will be processed to take part in the aggregation round.
    *
    * arguments:
    *   nbSamples (int16): The number of samples the weights have been trained on.
    *   weights (int48[numWeights]): List of new weights.  
    */
    function submitWeights(int nbSamples, int48[numWeights] memory weights) public payable{
        require(!participantsValue[msg.sender].participates, "Must not already be in current round of aggregation.");
        require(nbSamples>0, "Number of samples trained on must be greater than 0.");
        require(msg.value >= aggregationPrice, "Minimum required amount to participate is 5 ether.");
        // require(MAE(weights) < errorThreshold, "the error is to big.");
        participantsList.push(msg.sender);

        participantsValue[msg.sender].participates = true;
        participantsValue[msg.sender].samples = nbSamples;
        participantsValue[msg.sender].mae = MAE(weights);
        totalSamplesSubmitted+=nbSamples;

        if (participantsValue[msg.sender].mae < errorThreshold){
            participantsValue[msg.sender].accepted = true;
            currentParticipants ++;
            totalSamplesAccepted += nbSamples;
            processWeights(nbSamples, weights);
        }else{
            participantsValue[msg.sender].accepted = false;
        }
    }

    /*
    * Sets the initial weights and set the version to 1.
    * Can only be called in the beginning of the experiment.
    */
    function setInitWeights(int48[numWeights] memory weights) external{
        require(version == 0, "The weights have already been initialised.");
        currentWeights = weights;
        version++;
    }

    /*
    * Process the weights based on when they have been received. If they are the first
    * weights to be sent for a given aggregation round then the initNextWeights method 
    * will be called. if they are not the last weights to be sent, then the updateNextWeights
    * function will be called. Finally if they are the last weights to be aggregated in a 
    * given round then 3 functions will be called to conclude and reward the aggregation 
    * round.
    *
    * arguments:
    *   nbSamples (int16): The number of samples the weights have been trained on.
    *   weights (int48[numWeights]): List of new weights.  
    */
    function processWeights(int nbSamples, int48[numWeights] memory weights) private {
        if (1 < currentParticipants && currentParticipants < minParticipant){
            updateNextWeights(nbSamples, weights);
        }else if (currentParticipants == minParticipant) {
            updateCurrentWeights(nbSamples, weights);
            rewardWorkers();
            prepareNextAggregation();
        }else{
            initNextWeights(nbSamples, weights);
        }
    }

    /*
    * Rewards the participants based on their contribution (number of samples) and if their weights were accepted based on
    * the error function.
    * Each participant, if his weights were accepted, will be rewarded with :
    *   reward = (1 + s/sa - s/sb)*a [ether]
    * and if his weights were not accepted:
    *   reward = (1 - s/sb)*a [ether]
    * where :
    *   s : The samples the participant has sent.
    *   sa : The total number of samples of accepted weights for this round of aggregation.
    *   sb : The total number of samples for this round of aggregation.
    *   a : The aggregation price.
    */
    function rewardWorkers() private {
        for (uint8 i = 0; i < participantsList.length; i++){ 
            uint samples = uint(participantsValue[participantsList[i]].samples);
            if (participantsValue[participantsList[i]].accepted){
                payable(participantsList[i]).transfer(aggregationPrice + aggregationPrice*samples/uint(totalSamplesAccepted) - aggregationPrice*samples/uint(totalSamplesSubmitted));
            }
            else{
                payable(participantsList[i]).transfer(aggregationPrice - aggregationPrice*samples/uint(totalSamplesSubmitted));
            }
        }
    }

    /*
    * Cleans the variables for the next round of aggregation.
    *   Increases the values of the version by 1 (effectively updating it).
    *   Resets the current number of participants to 0.
    *   Resets the total amount of samples accepted to 0.    
    *   Resets the total amount of samples submitted to 0.
    *   Sets the peoples participates variable to False.
    *   Resets The liste of participants to empty.
    */
    function prepareNextAggregation() private {
        version ++;
        currentParticipants = 0;
        totalSamplesAccepted = 0;
        totalSamplesSubmitted = 0;
        resetParticipantsValue();
        delete participantsList;
    }

    /*
    * Rests the participantsValue.participates of all people that participated in the last round of aggregation
    * to false.
    */
    function resetParticipantsValue() private {
        for (uint8 i = 0; i < participantsList.length; i++){
            participantsValue[participantsList[i]].participates = false; //  normally only this should be sufficient
        }
    }

    /* 
    * Updates the next weights value with the new weights multiplied by the number of samples
    * they have been trained on.
    *
    * arguments:
    *   nbSamples (int16): The number of samples the weights have been trained on.
    *   weights (int48[numWeights]): List of new weights.  
    */ 
    function initNextWeights(int nbSamples, int48[numWeights] memory weights) private{
        for (uint16 i = 0; i < numWeights; i++) nextWeights[i] = weights[i]*int48(nbSamples);
    }

    /* 
    * Increases the next weights value with the new weights multiplied by the number of samples
    * they have been trained on.
    *
    * arguments:
    *   nbSamples (int16): The number of samples the weights have been trained on.
    *   weights (int48[numWeights]): List of new weights.  
    */ 
    function updateNextWeights(int nbSamples, int48[numWeights] memory weights) private{
        for (uint16 i = 0; i < numWeights; i++) nextWeights[i] += weights[i]*int48(nbSamples);
    }

    /*
    * Updates the currents weights with the last weights sent and the next weights that have been computed overtime.
    *
    * arguments:
    *   nbSamples (int16): The number of samples the weights have been trained on.
    *   weights (int48[numWeights]): List of new weights.  
    */
    function updateCurrentWeights(int nbSamples, int48[numWeights] memory weights) private{
        for (uint16 i = 0; i < numWeights; i++) currentWeights[i] = (nextWeights[i] + weights[i]*int48(nbSamples))/int48(totalSamplesAccepted);
    }

    
    // Mean Absolute Error
    function MAE(int48[numWeights] memory weights) public view returns (uint){
        uint mae = 0;
        for (uint16 i = 0; i < numWeights; i++) mae += AE(currentWeights[i], weights[i]);
        return mae/uint(numWeights);
    }

    // Mean Squared Error
    function MSE(int48[numWeights] memory weights) private view returns (uint){
        uint mse = 0;
        for (uint16 i = 0; i < numWeights; i++) mse += SE(currentWeights[i], weights[i]);
        return mse/uint(numWeights);
    }

    // Root Mean Squared Error 
    function RMSE(int48[numWeights] memory weights) private view returns (uint){
        uint rmse = MSE(weights);
        return sqrt(rmse);
    }

    // squared error
    function SE(int48 val1, int48 val2) private pure returns (uint){
        return uint48((val1 - val2)**2);
    }

    // absolute error
    function AE(int48 val1, int48 val2) private pure returns (uint){
        return uint(abs(val1 - val2));
    }

    // absolute function
    function abs(int48 x) private pure returns (int) {
        return x >= 0 ? x : -x;
    }

    // square root function
    function sqrt(uint x) private pure returns (uint y) {
        uint z = (x + 1) / 2;
        y = x;
        while (z < y) {
            y = z;
            z = (x / z + z) / 2;
        }
    }

    // returns the current weights
    function getWeights() external view returns(int48[numWeights] memory){
        return currentWeights;
    }

    // returns the address of the client making the call.
    function getAddress() external view returns (address) {
        return msg.sender;
    }

    function getMAE() external view returns (uint){
        return participantsValue[msg.sender].mae;
    }

    function getAccpeted() external view returns (bool){
        return participantsValue[msg.sender].accepted;
    }

    function getParticipated() external view returns (bool){
        return  participantsValue[msg.sender].participates;
    }
}