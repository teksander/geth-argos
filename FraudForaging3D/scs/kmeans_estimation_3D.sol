// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

contract ForagingPtManagement{

    uint constant space_size  = 3;
    uint constant num_pt      = 100;
    uint constant max_life    = 3;
    uint constant min_rep     = 0;     //Minimum number of reported points that make contract verified
    int256 constant radius    = 6000000;
    uint constant inflation_reward = 80000000000000000000; //inflation reward R, R/#winner
    uint constant min_cluster_deposit = 2; //minimum percentage of assets for new cluster init
    int256 constant max_unverified_cluster =  3;

    address public minter;
    mapping (address => uint) public balances; //Tracker of onchain deposit values

    struct Point{
        int[space_size] position;
        uint credit;   // deposited money in WEI
        uint category; // 0:non-food, 1:food
        int cluster;
        address sender;
        uint realType; // for debugging: the real category of the reported point
    }

    struct Cluster{
        int[space_size] position;
        uint life;
        uint verified;
        uint num_rep; //Number of reported points that supports this cluster
        uint256 total_credit; //Sum of deposited credit
        uint256 total_credit_food; //Sum of deposited credit that report this point as food
        uint256 realType; //real food/non food type of the Initially reported Point of the cluster, for experimental purpose only
        address init_reporter;
        uint256 intention; //intention = 0 initial report, intention > 0 verification of existing cluster No. intention-1
        int[space_size] sup_position;
        uint256 total_credit_outlier;
        address[] outlier_senders;
        uint block_verified;
    }

    struct clusterInfo{
        // int x;
        // int y;
        // int xo;
        // int yo;
        int[space_size] position;
        int[space_size] positiono;
        int256 minDistance;
        uint minClusterIdx;
        uint foundCluster;
        uint minClusterStatus;
    }

    int[4] report_statistics;
    uint256 public min_balance;
    // 0: number of recorded reports, 
    // 1: number of reports rejected due to duplicated verification, 
    // 2: number of reports rejected due to maximum number of clusters reached, 
    // 3: verification outlier count
    constructor() {
        report_statistics[0] = 0;
        report_statistics[1] = 0;
        report_statistics[2] = 0;
        report_statistics[3] = 0;
        min_balance = 53333333333333333333;
    }


    int[space_size] position_zeros;
    Point[] pointList;
    Cluster[] clusterList;
    clusterInfo info = clusterInfo(position_zeros,position_zeros,1e10,0,0,0);
    int256 unverfied_clusters = 0;
    //uint256 public min_balance = 53333333333333333333; //Minimum number of balance to confirm a cluster

    // function reportNewPt(int256 x, int256 y, uint category, uint256 amount, uint256 realType, uint256 intention) public payable{
    function reportNewPt(int256[space_size] memory position, uint category, uint256 amount, uint256 realType, uint256 intention) public payable{
        require(msg.value == amount);
        uint256 curtime = block.timestamp;

        //local variables for pointlist search
        uint c = 0;
        uint curLength = 0;
        if(min_balance==0){
            min_balance = 53333333333333333333;
        }

        int256[space_size] memory position_avg;
        //average of all supportive votes
        int256[space_size] memory position_sup_avg;

        int256 this_distance = 0;
        //mark clusters should be abandoned
        unverfied_clusters = 0;
        for (uint i=0; i<clusterList.length; i++){
            if (clusterList[i].verified==0){
                unverfied_clusters+=1;
            }
            if (unverfied_clusters>max_unverified_cluster){
                clusterList[i].verified=3;
            }
        }
        // Recluster all points k // can be skipped in certain task configurations
        for (uint k=0; k<pointList.length; k++){
            info.minDistance = 1e10;
            info.minClusterIdx = 0;
            info.foundCluster = 0;
            if (pointList[k].cluster >= 0 && clusterList[uint(pointList[k].cluster)].verified == 0){ //point[k].cluster may == -1
                    for (uint i=0; i<clusterList.length; i++){
                // Check if the newly reported pt belongs to any cluster
                if (clusterList[i].verified==0){ // Awaiting verification, only check clusters that are awaiting verification
                    for (uint j=0; j<space_size; j++){
                        position_avg[j] = ((int256(clusterList[i].position[j])*int256(clusterList[i].total_credit)
                                         + int256(pointList[k].position[j])*int256(amount)))/int256(clusterList[i].total_credit+amount);
                    }
                    if(pointList[k].category==1){
                        for (uint j=0; j<space_size; j++){
                        position_sup_avg[j] = ((int256(clusterList[i].sup_position[j])*int256(clusterList[i].total_credit_food)
                                         + int256(pointList[k].position[j])*int256(amount)))/int256(clusterList[i].total_credit_food+amount);
                        }
                    }
                    this_distance = getDistance(position_avg, pointList[k].position);

                    if (this_distance<info.minDistance){
                        info.minDistance = this_distance;
                        info.minClusterIdx = i;
                        info.foundCluster = 1;
                        info.position  = position_avg;
                        info.positiono = position_sup_avg;
                        info.minClusterStatus = clusterList[i].verified;
                    }
                }
            }
            // Update the membership to the nearest cluster of point[k]
            if (info.foundCluster ==1 && info.minClusterIdx != uint(pointList[k].cluster)){
                if (clusterList[uint(pointList[k].cluster)].total_credit_food>pointList[k].credit){ //At least another supportive vote in this cluster, other than the one of pointList[k]
                    for (uint j=0; j<space_size; j++){
                        clusterList[uint(pointList[k].cluster)].position[j] = ((int256(clusterList[uint(pointList[k].cluster)].position[j])*int256(clusterList[uint(pointList[k].cluster)].total_credit)
                                         - int256(pointList[k].position[j])*int256(pointList[k].credit)))/(int256(clusterList[uint(pointList[k].cluster)].total_credit-pointList[k].credit));
                    }
                }
                clusterList[uint(pointList[k].cluster)].num_rep-=1;
                clusterList[uint(pointList[k].cluster)].total_credit-=pointList[k].credit;


                if (pointList[k].category==1){
                    if (clusterList[uint(pointList[k].cluster)].total_credit_food>pointList[k].credit){
                        for (uint j=0; j<space_size; j++){
                        clusterList[uint(pointList[k].cluster)].sup_position[j] = ((int256(clusterList[uint(pointList[k].cluster)].sup_position[j])*int256(clusterList[uint(pointList[k].cluster)].total_credit_food)
                                         - int256(pointList[k].position[j])*int256(pointList[k].credit)))/(int256(clusterList[uint(pointList[k].cluster)].total_credit_food-pointList[k].credit));
                        }
                    }
                    clusterList[uint(pointList[k].cluster)].total_credit_food-=pointList[k].credit;

                }
                clusterList[info.minClusterIdx].num_rep+=1;
                clusterList[info.minClusterIdx].total_credit+=pointList[k].credit;
                clusterList[info.minClusterIdx].position = info.position;
                if (pointList[k].category==1){
                    clusterList[info.minClusterIdx].total_credit_food+=pointList[k].credit;
                    clusterList[info.minClusterIdx].sup_position = info.positiono;
                }
                pointList[k].cluster = int256(info.minClusterIdx);
                if (clusterList[uint(pointList[k].cluster)].total_credit_food == 0){ //when there is no more supportive votes in the cluster, due to kmeans reclustering
                        clusterList[uint(pointList[k].cluster)].verified=5; //cluster abandon due to supportive votes have been reassigned to other clusters
                    }
                }
            }
        }



        // Assign new point a cluster
        info.minDistance = 1e10;
        info.minClusterIdx = 0;
        info.foundCluster = 0;
        // this_distance = 0;
        // Does it need to go back to zeros?
        // int256[space_size] position_avg;
        // int256 this_distance = 0;

        if (category==1 && clusterList.length == 0){
            clusterList.push(Cluster(position, curtime+max_life, 0, 1, amount, amount, realType, msg.sender, intention, position, 0, new address[](0), 0));
            pointList.push(Point(position, amount, category, 0, msg.sender, realType));
            balances[msg.sender] += amount;
            report_statistics[0] += 1;
        }
        else{
            // Search for closest unverified cluster
            for (uint i=0; i<clusterList.length; i++){
                //Process cluster expirationamount
//                if (clusterList[i].verified==1 && clusterList[i].life<curtime){
//                    // verified cluster where credit is already redistributed
//                    clusterList[i].verified=2;
//                }
                //Check if the newly reported pt belongs to any cluster
                if (clusterList[i].verified==0){ //Cluster awaiting verification
                    for (uint j=0; j<space_size; j++){
                        position_avg[j] = ((int256(clusterList[i].position[j])*int256(clusterList[i].total_credit)
                                         + int256(position[j])*int256(amount)))/int256(clusterList[i].total_credit+amount);
                    }
                    if(category==1){
                        for (uint j=0; j<space_size; j++){
                        position_sup_avg[j] = ((int256(clusterList[i].sup_position[j])*int256(clusterList[i].total_credit_food)
                                         + int256(position[j])*int256(amount)))/int256(clusterList[i].total_credit_food+amount);
                        }
                    }
                    this_distance = getDistance(position_avg, position);

                    if (this_distance<=radius && this_distance<info.minDistance){
                        info.minDistance = this_distance;
                        info.minClusterIdx = i;
                        info.foundCluster = 1;
                        // info.x=x_avg;
                        // info.y=y_avg;
                        // info.xo = x;
                        // info.yo = y;
                        info.position  = position_avg;
                        info.positiono = position_sup_avg;
                        info.minClusterStatus = clusterList[i].verified;
                    }
                }
            }

            //if the report is not close enough to the cluster center that the robot intends to verify:
            if(intention>0 && info.foundCluster==1 && info.minClusterIdx!=intention-1 &&clusterList[intention-1].verified==0){
                bool senderExists = false;
                for (uint j = 0; j < clusterList[intention-1].outlier_senders.length; j++) {
                    if (clusterList[intention-1].outlier_senders[j] == msg.sender) {
                        senderExists = true;
                    }
                }
                //has successful verification to this cluster before
                for (uint j = 0; j < pointList.length; j++) {
                    if (pointList[j].cluster == int256(intention-1) && pointList[j].sender == msg.sender) {
                        senderExists = true;
                    }
                }

                if (!senderExists){
                    clusterList[intention-1].total_credit_outlier+=amount;
                    clusterList[intention-1].outlier_senders.push(msg.sender);
                }
            }
            //if exists non-verified cluster that the new point belongs
            if (info.foundCluster==1 && info.minClusterStatus == 0 && clusterList[info.minClusterIdx].init_reporter != msg.sender){
                uint repexist = 0; //check if report from the same agent already exist in this cluster
                for (uint k=0; k<pointList.length-1; k++){
                    if(pointList[k].cluster == int256(info.minClusterIdx) && pointList[k].sender==msg.sender){
                        repexist=1;
                    }
                }
                if(repexist==0){
                    clusterList[info.minClusterIdx].num_rep+=1;
                    clusterList[info.minClusterIdx].total_credit+=amount;
                    //clusterList[info.minClusterIdx].total_uncertainty+=uncertainty;
                    if (category==1){
                        clusterList[info.minClusterIdx].total_credit_food+=amount;
                        clusterList[info.minClusterIdx].sup_position = info.positiono;
                    }

                    // clusterList[info.minClusterIdx].x = info.x;
                    // clusterList[info.minClusterIdx].y = info.y;
                    clusterList[info.minClusterIdx].position = info.position;

                    //ADD CORRESPONDING POINT
                    pointList.push(Point(position, 0, category, int256(info.minClusterIdx), msg.sender, realType));
                    pointList[pointList.length-1].credit+=amount;
                    balances[msg.sender] += amount;
                    report_statistics[0] += 1;
                }
                else{
                    payable(msg.sender).transfer(amount);
                    report_statistics[1] += 1; // report removed due to redundant verification
                }
            }
            else if (category==1 && info.foundCluster==0 && unverfied_clusters<max_unverified_cluster && amount>min_cluster_deposit){
                //if point reports a food source position and  belongs to nothing>inter cluster threshold, create new cluster
                clusterList.push(Cluster(position,curtime + max_life, 0, 1, amount, amount, realType, msg.sender, intention,position, 0, new address[](0), 0));
                pointList.push(Point(position,0, category, int256(clusterList.length-1), msg.sender, realType));
                pointList[pointList.length-1].credit+=amount;
                balances[msg.sender] += amount;
                report_statistics[0] += 1;

            }
            else{
                //Do nothing and transfer back, if anything else
                payable(msg.sender).transfer(amount);
                report_statistics[2] += 1; //report removed due to maximum number of unverified cluster reached
            }
        }
        // Unique report
        for (uint i=0; i<clusterList.length; i++){
            if (clusterList[i].verified==0){
                for (uint k=0; k<pointList.length-1; k++){
                    for (uint l=k+1; l<pointList.length; l++){
                        if (pointList[k].cluster == int256(i) && pointList[l].cluster == int256(i) && pointList[k].sender == pointList[l].sender && pointList[k].category == pointList[l].category){
                            payable(pointList[l].sender).transfer(pointList[l].credit);
                            clusterList[i].num_rep-=1;
                            clusterList[i].total_credit-=pointList[l].credit;
                            if (pointList[l].category==1){
                                clusterList[i].total_credit_food-=pointList[l].credit;
                            }
                            balances[pointList[l].sender] -= pointList[l].credit;
                            pointList[l] = pointList[pointList.length-1];
                            pointList.pop();
                            report_statistics[1] += 1; // report removed due to redundant verification
                            report_statistics[0] -= 1;
                         }
                    }
                }
            }

        }
        //remove all points with cluster = -1
        c = 0;
        curLength = pointList.length;
        while(c<curLength){
            if (pointList[c].cluster==-1){
                pointList[c] = pointList[pointList.length-1];
                pointList.pop();
                curLength = pointList.length;
            }
            else{
                c+=1;
            }
        }

        //If cluster receives enough samples, verified.
        uint256 total_non_food_credit = 0;
        uint256 bonus_credit = 0;
        uint256 inflation_credit = 0;
        uint256 remaining_inf_credit = 0;
        for(uint i=0; i<clusterList.length; i++){
            if (clusterList[i].verified==0 && clusterList[i].num_rep>=min_rep && clusterList[i].total_credit>=(min_balance*95/100) && clusterList[i].total_credit_food>(clusterList[i].total_credit-clusterList[i].total_credit_food)){
                clusterList[i].verified=1; //cluster verified
                clusterList[i].block_verified = block.number;
                clusterList[i].life = curtime+max_life;
                total_non_food_credit = clusterList[i].total_credit-clusterList[i].total_credit_food;
                //Redistribute money
                uint256 food_num =0;
                uint256 non_food_num =0;
                for (uint j=0; j<pointList.length; j++){
                    if (pointList[j].cluster == int256(i) && pointList[j].category ==1){
                        food_num+=1;
                     }
                    else{
                        non_food_num+=1;
                    }
                }
                inflation_credit = inflation_reward/food_num; //inflation credit
                min_balance+=(inflation_reward*2/3)/uint(max_unverified_cluster); //min balance inflation
                for (uint j=0; j<pointList.length; j++){
                    if (pointList[j].cluster == int256(i) && pointList[j].category ==1){
                    remaining_inf_credit = inflation_credit; //amount of credit to be transferred back to robot wallet
                        //bonus_credit = total_non_food_credit*pointList[j].credit/clusterList[info.minClusterIdx].total_credit_food;
                        if (food_num>0){
                            bonus_credit = total_non_food_credit/food_num;
                        }
                        else{
                            bonus_credit = 0;
                        }
                        //search for open reports from the same robot, inflate their deposits
                        for (uint k=0; k<clusterList.length; k++){
                            if(clusterList[k].verified == 0 && k!=i){
                                for (uint l=0; l<pointList.length; l++){
                                    if (pointList[l].cluster == int256(k) && pointList[l].sender == pointList[j].sender){
                                        pointList[l].credit+=(inflation_credit/uint(max_unverified_cluster));
                                        balances[pointList[l].sender] += (inflation_credit/uint(max_unverified_cluster));
                                        clusterList[k].total_credit+=(inflation_credit/uint(max_unverified_cluster));
                                        if(pointList[l].category ==1){
                                            clusterList[k].total_credit_food+=(inflation_credit/uint(max_unverified_cluster));
                                        }
                                        remaining_inf_credit-=(inflation_credit/uint(max_unverified_cluster));
                                    }
                                }
                            }
                        }
                        //search for open reports from the same robot, inflate their deposits
//                        for (uint k=0; k<pointList.length; k++){
//                                if (pointList[k].sender == pointList[j].sender && pointList[k].cluster  != int256(i) && pointList[k].cluster<int(clusterList.length) && pointList[k].cluster >=0){
//                                    if(clusterList[uint(pointList[k].cluster)].verified == 0){
//                                        pointList[k].credit+=(inflation_credit/uint(max_unverified_cluster));
//                                        balances[pointList[k].sender] += (inflation_credit/uint(max_unverified_cluster));
//                                        clusterList[uint(pointList[k].cluster)].total_credit+=(inflation_credit/uint(max_unverified_cluster));
//                                        if(pointList[k].category ==1){
//                                            clusterList[uint(pointList[k].cluster)].total_credit_food+=(inflation_credit/uint(max_unverified_cluster));
//                                        }
//                                        if(remaining_inf_credit>=(inflation_credit/uint(max_unverified_cluster))){
//                                            remaining_inf_credit-=(inflation_credit/uint(max_unverified_cluster));
//                                        }
//                                        //remaining_inf_credit = inflation_credit; //amount of credit to be transferred back to robot wallet
//                                    }
//
//                            }
//                        }

                        payable(pointList[j].sender).transfer(bonus_credit+pointList[j].credit+remaining_inf_credit);
                     }
//                    else if(pointList[j].cluster == int256(i) && pointList[j].category ==0){
//                        //search for open reports from the same robot, inflate their deposits
//                        for (uint k=0; k<pointList.length; k++){
//                                if (pointList[k].sender == pointList[j].sender && pointList[k].cluster  != int256(i) && int(clusterList.length)>pointList[k].cluster && pointList[k].cluster >=0 && clusterList[uint(pointList[k].cluster)].verified == 0){
//                                pointList[k].credit+=inflation_credit/uint(max_unverified_cluster);
//                                clusterList[uint(pointList[k].cluster)].total_credit+=inflation_credit/uint(max_unverified_cluster);
//                                if(pointList[k].category ==1){
//                                    clusterList[uint(pointList[k].cluster)].total_credit_food+=inflation_credit/uint(max_unverified_cluster);
//                                }
//                                //remaining_inf_credit-=inflation_credit/uint(max_unverified_cluster);
//                            }
//                        }
//                        //payable(pointList[j].sender).transfer(remaining_inf_credit);  //losing coalition, transfer only inflation credit
//                    }

                }
                c = 0;
                curLength = pointList.length;
                while(c<curLength){
                    if (pointList[c].cluster == int256(i) || pointList[c].cluster==-1){
                        if(pointList[c].cluster == int256(i)){
                            balances[pointList[c].sender] -= pointList[c].credit;
                        }
                        pointList[c] = pointList[pointList.length-1];
                        pointList.pop();
                        curLength = pointList.length;
                    }
                    else{
                        c+=1;
                    }
                }
            }
            else if (clusterList[i].verified==0 && clusterList[i].num_rep>=min_rep && clusterList[i].total_credit>=(min_balance*95/100) && clusterList[i].total_credit_food<(clusterList[i].total_credit-clusterList[i].total_credit_food)){
                clusterList[i].verified=2; //cluster abandon
                clusterList[i].block_verified = block.number;
                total_non_food_credit = clusterList[i].total_credit-clusterList[i].total_credit_food;
                //Redistribute money
                //WVG wining side
                uint256 non_food_num =0;
                uint256 food_num=0;
                for (uint j=0; j<pointList.length; j++){
                    if (pointList[j].cluster == int256(i) && pointList[j].category ==0){
                        non_food_num+=1;
                     }
                    else{
                        food_num+1;
                    }
                }
                inflation_credit = inflation_reward/non_food_num; //inflation credit
                min_balance+=(inflation_reward*2/3)/uint(max_unverified_cluster); //min balance inflation
                for (uint j=0; j<pointList.length; j++){
                    if (pointList[j].cluster == int256(i) && pointList[j].category ==0){
                    remaining_inf_credit = inflation_credit; //amount of credit to be transferred back to robot wallet
                        // bonus_credit = clusterList[i].total_credit_food*pointList[j].credit/total_non_food_credit;
                        if (non_food_num>0){
                            bonus_credit = clusterList[i].total_credit_food/non_food_num;
                        }
                        else{
                            bonus_credit = 0;
                        }
                        //search for open reports from the same robot, inflate their deposits
                        for (uint k=0; k<clusterList.length; k++){
                            if(clusterList[k].verified == 0 && k!=i){
                                for (uint l=0; l<pointList.length; l++){
                                    if (pointList[l].cluster == int256(k) && pointList[l].sender == pointList[j].sender){
                                        pointList[l].credit+=(inflation_credit/uint(max_unverified_cluster));
                                        balances[pointList[l].sender] += (inflation_credit/uint(max_unverified_cluster));
                                        clusterList[k].total_credit+=(inflation_credit/uint(max_unverified_cluster));
                                        if(pointList[l].category ==1){
                                            clusterList[k].total_credit_food+=(inflation_credit/uint(max_unverified_cluster));
                                        }
                                        remaining_inf_credit-=(inflation_credit/uint(max_unverified_cluster));
                                    }
                                }
                            }
                        }
//                        //search for open reports from the same robot, inflate their deposits
//                        for (uint k=0; k<pointList.length; k++){
//                                if (pointList[k].sender == pointList[j].sender && pointList[k].cluster  != int256(i) && int(clusterList.length)>pointList[k].cluster && pointList[k].cluster >=0){
//                                    if(clusterList[uint(pointList[k].cluster)].verified == 0){
//                                        pointList[k].credit+=(inflation_credit/uint(max_unverified_cluster));
//                                        balances[pointList[k].sender] += (inflation_credit/uint(max_unverified_cluster));
//                                        clusterList[uint(pointList[k].cluster)].total_credit+=(inflation_credit/uint(max_unverified_cluster));
//                                        if(pointList[k].category ==1){
//                                            clusterList[uint(pointList[k].cluster)].total_credit_food+=(inflation_credit/uint(max_unverified_cluster));
//                                        }
//                                        if(remaining_inf_credit>=(inflation_credit/uint(max_unverified_cluster))){
//                                            remaining_inf_credit-=(inflation_credit/uint(max_unverified_cluster));
//                                        }
//                                    //remaining_inf_credit = inflation_credit; //amount of credit to be transferred back to robot wallet
//                                    }
//
//                            }
//                        }
                        payable(pointList[j].sender).transfer(bonus_credit+pointList[j].credit+remaining_inf_credit);
                     }
//                    else if(pointList[j].cluster == int256(i) && pointList[j].category ==1){
//                        //search for open reports from the same robot, inflate their deposits
//                        for (uint k=0; k<pointList.length; k++){
//                                if (pointList[k].sender == pointList[j].sender && pointList[k].cluster  != int256(i) && int(clusterList.length)>pointList[k].cluster && pointList[k].cluster >=0 && clusterList[uint(pointList[k].cluster)].verified == 0){
//                                pointList[k].credit+=inflation_credit/uint(max_unverified_cluster);
//                                clusterList[uint(pointList[k].cluster)].total_credit+=inflation_credit/uint(max_unverified_cluster);
//                                if(pointList[k].category ==1){
//                                    clusterList[uint(pointList[k].cluster)].total_credit_food+=inflation_credit/uint(max_unverified_cluster);
//                                }
//                                //remaining_inf_credit-=inflation_credit/uint(max_unverified_cluster);
//                            }
//                        }
//                        //payable(pointList[j].sender).transfer(remaining_inf_credit); //losing coalition, transfer only inflation credit
//                    }
                }
                //remove points
                c = 0;
                curLength = pointList.length;
                while(c<curLength){
                    if (pointList[c].cluster == int256(i) || pointList[c].cluster==-1){
                        if(pointList[c].cluster == int256(i)){
                            balances[pointList[c].sender] -= pointList[c].credit;
                        }
                        pointList[c] = pointList[pointList.length-1];
                        pointList.pop();
                        curLength = pointList.length;

                    }
                    else{
                        c+=1;
                    }
                }
            }
            else if (clusterList[i].verified==0 && clusterList[i].total_credit_outlier>(min_balance/2)){ //min_balance/2 = 1/3 of total assets, as min_balance = 2/3 total assets
                for (uint j=0; j<clusterList[i].outlier_senders.length; j++){
                    bonus_credit = clusterList[i].total_credit/clusterList[i].outlier_senders.length;
                    payable(clusterList[i].outlier_senders[j]).transfer(bonus_credit);
                }
                clusterList[i].verified=4; //cluster rejected due to most of reports that intended to verify it have been classified as outliers
            }
            else if (clusterList[i].verified==0 && clusterList[i].total_credit<min_cluster_deposit){ //assets in cluster below minimum threshold
                clusterList[i].verified=5; //cluster abandon due to the sum of reports' deposit below minimum deposit
            }
            //remove points that correspond to redundant or rejected clusters
            if (clusterList[i].verified==3 || clusterList[i].verified==4 || clusterList[i].verified==5){
                for (uint j=0; j<pointList.length; j++){
                    if (pointList[j].cluster == int256(i) && clusterList[i].verified==3){ //only return deposits for clusters that have been rejected due to maximum number of cluster reached and condition here
                        payable(pointList[j].sender).transfer(pointList[j].credit);
                     }
                }
                //remove points
                c = 0;
                curLength = pointList.length;
                while(c<curLength){
                    if (pointList[c].cluster == int256(i)){
                        if(pointList[c].cluster == int256(i)){
                            balances[pointList[c].sender] -= pointList[c].credit;
                        }
                        pointList[c] = pointList[pointList.length-1];
                        pointList.pop();
                        curLength = pointList.length;
                    }
                    else{
                        c+=1;
                    }
                }
            }
        }



    }

    //----- setters and getters ------

    function getClusters() public view returns(Cluster[] memory) { return clusterList; }
    function getClusterKeys() public pure returns (string[13] memory){
        return ["position",
            "life",
            "verified",
            "num_rep",
            "total_credit",
            "total_credit_food",
            "realType",
            "init_reporter",
            "intention",
            "sup_position",
            "total_credit_outlier",
            "outlier_senders",
            "block_verified"];
        }

    function getPoints() public view returns(Point[] memory) { return pointList; }
    function getPointKeys() public pure returns (string[6] memory){
        return ["position",
            "credit",
            "category",
            "cluster",
            "sender",
            "realType"];
        }

    function getSourceList() public view returns(Cluster[] memory){
        return clusterList;
    }
    function getClusterInfo() public view returns(clusterInfo memory){
        return info;
    }
    function getPointListInfo() public view returns(Point[]  memory){
        return pointList;
    }
    function getReportStatistics() public view returns (int[4] memory) {
        return report_statistics;
    }
    //------ pure functions (math) ------

    function getDistance2D(int256 _x1, int256 _x2, int256 _y1, int256 _y2) private pure returns(int256) {
        // Return a distance measure in 2D space
        return sqrt(((_x2 - _x1)**2) + ((_y2 - _y1)**2));
    }

    function getDistance(int256[space_size] memory _p1, int256[space_size] memory _p2) private pure returns(int256) {
        // Return a distance measure in generic dimensions
        int256 sqsum = 0;
        for (uint j=0; j<space_size; j++){
            sqsum += (_p2[j]-_p1[j])**2;
        }
        return sqrt(sqsum);
    }
    function colourBGRDistance(int256[space_size] memory _p1, int256[space_size] memory _p2) public pure returns (int256) {

        int256 divisor = 100000;
        int256[space_size] memory _rp1;
        int256[space_size] memory _rp2;
        for (uint256 i = 0; i < space_size; i++) {
            int256 rounded = _p1[i]/ divisor;

            if (rounded < 0) {
                rounded = 0;
            }
            _rp1[i] = rounded;
            rounded = _p2[i]/ divisor;
            if (rounded < 0) {
                rounded = 0;
            }
            _rp2[i] = rounded;
        }

        int256 rMean = (int256(_rp1[2]) + int256(_rp2[2])) / 2;
        int256 r = int256(_rp1[2]) - int256(_rp2[2]);
        int256 g = int256(_rp1[1]) - int256(_rp2[1]);
        int256 b = int256(_rp1[0]) - int256(_rp2[0]);
        int256 distance = ((((512 + rMean) * r * r) >> 8) + 4 * g * g + (((767 - rMean) * b * b) >> 8));
        distance=sqrt(distance)*100000;
        return distance;
    }


    function sqrt(int256 _kx) private pure returns (int256 _ky) {
        // Return an approximation of the sqrt
        int256 _kz = (_kx + 1) / 2;
        _ky = _kx;
        while (_kz < _ky) {
            _ky = _kz;
            _kz = (_kx / _kz + _kz) / 2;
        }
    }

    function abs(int256 _k) private pure returns (int256) {
        // Return the absolute value
        return _k >= 0 ? _k : -_k;
    }
}