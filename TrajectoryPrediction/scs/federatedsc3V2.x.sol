// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FederatedLearning {
    uint8 constant numParticipants = ${MAXWORKERS}; // number of robots in an experiment
    uint8 constant minParticipant = numParticipants/2; // number of participant required for a round of aggregation
    uint constant aggregationPrice = 5 ether; // the price in wei of an aggregation round (to have in either divide by 10e17) (note : normally 1 ether = 10e18)
    uint constant errorThreshold = 50000000; // threshold value over which weights are not considered valid and won't be used for an aggregation round. max(MAE of good robot) = 10**7
    uint constant decay = 10**9;

    int[minParticipant] rankWeights; //[int(5), int(4), int(3), int(2), int(1), int(-1), int(-2)];
    // uint constant goodRobotCount = 5;
    // int[minParticipant] rankWeights = [int(2*10**8), int(1*10**8), int(-1*10**8)];

    uint16 constant numWeights = 2848; // number of weights of the neural networks
    int48[numWeights] currentWeights; // the last valid aggregated weights from the previous round
    int48[numWeights] nextWeights; // the nextweights (note : the new weights are continously added to the nextweights to reduce the amount of gas per call)

    address[] participantsList; // the participants of a round of aggregation
    address[] acceptedList;
    address[] previousParticipants;

    int totalSamplesAccepted; // the sum of the number of samples of the weights that have been accepted for an aggregation round
    int totalSamplesSubmitted; // the sum of the number of samples of all the weights that have been submitted for an aggregation round

    uint8 currentParticipants; // The current number of participants for an aggregation round 
    uint8 public version; // the version (the number of aggregation round that took place) of the currentWeights.
    

    struct Participant {
        int samples; // the number of samples associated to the wieghts of this participant
        bool participates; // if he is participating in the current round of aggregation
        uint mae;
        int money;
    }

    struct ranker{
        uint mae;
        uint index;
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
        participantsList.push(msg.sender);

        participantsValue[msg.sender].participates = true;
        participantsValue[msg.sender].samples = nbSamples;
        participantsValue[msg.sender].mae = MAE(weights);
        totalSamplesSubmitted+=nbSamples;

        if (participantsValue[msg.sender].mae < errorThreshold){
            acceptedList.push(msg.sender);
            currentParticipants ++;
            totalSamplesAccepted += nbSamples;
            processWeights(nbSamples, weights);
        }
        else {
            participantsValue[msg.sender].money -= 5*10**18;
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
    * Rewards the participants based on their contribution (number of samples) and their rank (based on the error function).
    * (only if their weights were accepted in the first place.)
    * Each participant, based on their rank, will either be rewarded positively with :
    *   reward = (1 + gr)*a [ether]
    * or ngatively with:
    *   reward = (1 - br)*a [ether]
    * where :
    *   gr : the good ratio of a participant
    *   br : the bad ratio of a participant
    *   a : The aggregation price.
    */
    function rewardWorkers() private {
        uint[minParticipant] memory rank = getRank();
        
        uint goodRobotCount = 0;
        for (uint8 i = 0; i < minParticipant; i++) if (rankWeights[i] > 0) goodRobotCount ++; 

        require(goodRobotCount > 0, "goodrobotcount should be greater than 0");
        require(goodRobotCount < minParticipant, "goodrobotcount should be smaller than total number of participants");

        

        int[] memory goodWeights = new int[](goodRobotCount);
        int[] memory badWeights = new int[](minParticipant-goodRobotCount);

        uint a; 
        uint b;
        for (uint8 i = 0; i < minParticipant; i++) {
            if (rank[i] < goodRobotCount){
                goodWeights[a] = participantsValue[acceptedList[i]].samples * rankWeights[rank[i]];
                a++;
            }else{
                badWeights[b] = participantsValue[acceptedList[i]].samples * rankWeights[rank[i]];
                b++;
            }
        }
        
        goodWeights = normalize(goodWeights, goodRobotCount);
        badWeights = normalize(badWeights, minParticipant-goodRobotCount);
        
        a=0;
        b=0;
        uint p = uint(participantsList.length);
        while (a+b<uint(minParticipant)){
            if (rank[a+b] < goodRobotCount){
                payable(acceptedList[a+b]).transfer(aggregationPrice*p/uint(currentParticipants) + aggregationPrice*decay*uint(goodWeights[a])/(10**18));
                participantsValue[acceptedList[a+b]].money += int(5*10**18*p/uint(currentParticipants) + 5*decay*uint(goodWeights[a]) - 5*10**18);
                a++;
            }else{
                payable(acceptedList[a+b]).transfer(aggregationPrice*p/uint(currentParticipants) - aggregationPrice*decay*uint(badWeights[b])/(10**18));
                participantsValue[acceptedList[a+b]].money += int(5*10**18*p/uint(currentParticipants) - 5*decay*uint(badWeights[b])) - 5*10**18;
                b++;
            }
        }
        
    }

    //becarfull as there are no floating point values in solidy, the values are normalized such
    //that the sum of all the values is equal to 10**9.
    function normalize(int[] memory data, uint length) private pure returns(int[] memory){
        int total = 0;
        int[] memory normalized = new int[](length);
        for (uint i = 0; i < length; i++) {
            normalized[i] = data[i] * 10**9;
            total = total + data[i];
        } 
        for (uint i = 0; i < length; i++) normalized[i] = normalized[i]/total;
        return normalized;
    }

    /*
    * returns the rank of the accepted participants.
    * performs a ranking based on the distance from the median MAE of this round of aggregation.
    * ex : mae = [10, 30, 0] (distance to median = [0, 20, 10])
    * return rank = [0, 2, 1]
    * with 0 being the best rank and rank.length - 1 being the worst.
    */
    function getRank() private view returns (uint[minParticipant] memory){
        uint[] memory mae = new uint[](minParticipant);
        uint[] memory mae_copy = new uint[](minParticipant);
        for (uint i=0; i < minParticipant; i++) {
            mae[i] = participantsValue[acceptedList[i]].mae;
            mae_copy[i] = participantsValue[acceptedList[i]].mae;
        }

        uint med = median(mae_copy);
        
        ranker[] memory rankers = new ranker[](minParticipant);
        for (uint i=0; i < minParticipant; i++){
            rankers[i].mae = uint(abs256(int(mae[i])-int(med)));
            rankers[i].index = i;
        }

        // rankers = sortComposed(rankers);
        quickSortComposed(rankers, int(0), int(uint(minParticipant) - 1));
        uint[minParticipant] memory rank;
        for (uint i=0; i < minParticipant; i++){
            rank[rankers[i].index] = i;
        }
        return rank;
    }

    // returns the median value of a list
    function median(uint[] memory my_list) public pure returns (uint med){
        my_list = sort(my_list);
        uint midr = my_list.length / 2;
        uint midl = my_list.length - midr -1;
        med = (my_list[midl] + my_list[midr])/2;
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
        previousParticipants = acceptedList;
        delete participantsList;
        delete acceptedList;
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

    // absolute function
    function abs256(int x) private pure returns (int) {
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

    function sort(uint[] memory data) private pure returns(uint[] memory) {
       quickSort(data, int(0), int(data.length - 1));
       return data;
    }
    
    function quickSort(uint[] memory arr, int left, int right) private pure{
        int i = left;
        int j = right;
        if(i==j) return;
        uint pivot = arr[uint(left + (right - left) / 2)];
        while (i <= j) {
            while (arr[uint(i)] < pivot) i++;
            while (pivot < arr[uint(j)]) j--;
            if (i <= j) {
                (arr[uint(i)], arr[uint(j)]) = (arr[uint(j)], arr[uint(i)]);
                i++;
                j--;
            }
        }
        if (left < j)
            quickSort(arr, left, j);
        if (i < right)
            quickSort(arr, i, right);
    }

    function sortComposed(ranker[] memory data) private pure returns(ranker[] memory) {
       quickSortComposed(data, int(0), int(data.length - 1));
       return data;
    }
    
    function quickSortComposed(ranker[] memory arr, int left, int right) private pure {
        int i = left;
        int j = right;
        if(i==j) return;
        uint pivot = arr[uint(left + (right - left) / 2)].mae;
        while (i <= j) {
            while (arr[uint(i)].mae < pivot) i++;
            while (pivot < arr[uint(j)].mae) j--;
            if (i <= j) {
                (arr[uint(i)], arr[uint(j)]) = (arr[uint(j)], arr[uint(i)]);
                i++;
                j--;
            }
        }
        if (left < j)
            quickSortComposed(arr, left, j);
        if (i < right)
            quickSortComposed(arr, i, right);
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

    function getAcceptedList() external view returns(address[] memory){
        return acceptedList;
    }

    function getParticipantsList() external view returns (address[] memory){
        return participantsList;
    }

    function getParticipated() external view returns (bool){
        return  participantsValue[msg.sender].participates;
    }

    function getRankWeight() external view returns (int[minParticipant] memory){
        return rankWeights;
    }

    function getPreviousParticipants() external view returns (address[] memory){
        return previousParticipants;
    }

    function getMoney() external view returns (int){
        return participantsValue[msg.sender].money;
    }

    function getBlockNumber() external view returns (uint){
        return block.number-1;
    }

    function getBlockHash() external view returns (bytes32){
        return blockhash(block.number-1);
    }

    function getPreviousBlockHash() external view returns (bytes32){
        return blockhash(block.number-2);
    }
}