// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

contract ForagingPtManagement{
    uint constant num_pt = 100;
    uint constant max_life = 100;
    uint constant min_rep = 10; //Minimum number of reported points that make contract verified
    int256 constant radius = 10000;

    address public minter;
    mapping (address => uint) public balances;

    struct Point{
        int x;
        int y;
        uint credit; //deposited money in WEI
        uint category; //0:non food, 1:food
        uint cluster;
        address sender;
        uint uncertainty;
    }

    struct Cluster{
        int x;
        int y;
        uint life;
        uint verified;
        uint num_rep; //Number of reported points that supports this cluster
        uint256 total_credit; //Sum of deposited credit
        uint256 total_credit_food; //Sum of deposited credit that report this point as food
        uint256 total_uncertainty; //Total reported uncertainty
    }

    struct clusterInfo{
        int x;
        int y;
        int xo;
        int yo;
        int256 minDistance;
        uint minClusterIdx;
        uint foundCluster;
        uint minClusterStatus;
    }
    Point[] pointList;
    Cluster[] clusterList;
    clusterInfo info = clusterInfo(0,0,0,0,1e10,0,0,0);

    function getDistance(int256 _x1, int256 _x2, int256 _y1, int256 _y2) private pure returns(int256) {
        //5 digits floating num_pt
        return sqrt(((_x2 - _x1)**2) + ((_y2 - _y1)**2));
        //return abs(_x1-_x2)+abs(_y1-_y2);
    }

    function sqrt(int256 _kx) private pure returns (int256 _ky) {
      int256 _kz = (_kx + 1) / 2;
        _ky = _kx;
        while (_kz < _ky) {
            _ky = _kz;
            _kz = (_kx / _kz + _kz) / 2;
        }
      }
    function abs(int256 _k) private pure returns (int256) {
    return _k >= 0 ? _k : -_k;
    }


    function reportNewPt(int256 x, int256 y, uint category, uint256 amount, uint256 uncertainty) public payable{
        require(msg.value == amount);
        uint256 curtime = block.timestamp;
        // Assign point a cluster
        info.minDistance = 1e10;
        info.minClusterIdx = 0;
        info.foundCluster = 0;
        int256 x_avg = 0;
        int256 y_avg = 0;
        int256 this_distance = 0;
        if (category==1 && clusterList.length == 0){
            clusterList.push(Cluster(x,y, curtime+max_life, 0, 1, amount, amount, uncertainty));
            pointList.push(Point(x,y,amount, category, 0, msg.sender, uncertainty));
        }
        else{
            // Search for closest unverified cluster
            for (uint i=0; i<clusterList.length; i++){
                //Process cluster expiration
                //clusterList[i].life-=1;
                if (clusterList[i].verified==1 && clusterList[i].life<curtime){
                    // verified cluster where credit is already redistributed
                    clusterList[i].verified=2;
                }
                //Check if the newly reported pt belongs to any cluster
                if (clusterList[i].verified!=2){ //Not abandoned cluster
                    x_avg = (int256(clusterList[i].x)*int256(clusterList[i].total_credit)+ int256(x)*int256(amount))/int256(clusterList[i].total_credit+amount);
                    y_avg = (int256(clusterList[i].y)*int256(clusterList[i].total_credit)+ int256(y)*int256(amount))/int256(clusterList[i].total_credit+amount);
                    this_distance = getDistance(x_avg, x, y_avg,  y);
                    if (this_distance<=radius && this_distance<info.minDistance){
                        info.minDistance = this_distance;
                        info.minClusterIdx = i;
                        info.foundCluster = 1;
                        info.x=x_avg;
                        info.y=y_avg;
                        info.xo = x;
                        info.yo = y;
                        info.minClusterStatus = clusterList[i].verified;
                    }
                    else if (info.foundCluster == 0){
                        //only for debugging purpose
                        info.minDistance = this_distance;
                        info.minClusterIdx = i;
                        info.foundCluster = 0;
                        info.x=x_avg;
                        info.y=y_avg;
                        info.xo = x;
                        info.yo = y;
                        info.minClusterStatus = clusterList[i].verified;
                    }
                }
            }

            //if exists non-verified cluster that the new point belongs
            if (info.minClusterStatus == 0 && info.foundCluster==1){

                clusterList[info.minClusterIdx].num_rep+=1;
                clusterList[info.minClusterIdx].total_credit+=amount;
                clusterList[info.minClusterIdx].total_uncertainty+=uncertainty;
                if (category==1){
                    clusterList[info.minClusterIdx].total_credit_food+=amount;
                }

                clusterList[info.minClusterIdx].x = info.x;
                clusterList[info.minClusterIdx].y = info.y;
                //ADD CORRESPONDING POINT
                pointList.push(Point(x,y,amount, category, info.minClusterIdx, msg.sender, uncertainty));


                //If cluster receives enough samples, verified.
                uint256 total_non_food_credit = 0;
                uint256 bonus_credit = 0;
                if (clusterList[info.minClusterIdx].num_rep>=min_rep && clusterList[info.minClusterIdx].total_credit_food>(clusterList[info.minClusterIdx].total_credit-clusterList[info.minClusterIdx].total_credit_food)){
                    clusterList[info.minClusterIdx].verified=1; //cluster verified
                    total_non_food_credit = clusterList[info.minClusterIdx].total_credit-clusterList[info.minClusterIdx].total_credit_food;
                    //Redistribute money
                    for (uint j=0; j<pointList.length; j++){
                        if (pointList[j].cluster == info.minClusterIdx && pointList[j].category ==1){
                            bonus_credit = total_non_food_credit*pointList[j].credit/clusterList[info.minClusterIdx].total_credit_food;
                            payable(pointList[j].sender).transfer(bonus_credit+pointList[j].credit);
                         }
                    }
                }
                else if (clusterList[info.minClusterIdx].num_rep>=min_rep && clusterList[info.minClusterIdx].total_credit_food<(clusterList[info.minClusterIdx].total_credit-clusterList[info.minClusterIdx].total_credit_food)){
                    clusterList[info.minClusterIdx].verified=2; //cluster abandon
                    total_non_food_credit = clusterList[info.minClusterIdx].total_credit-clusterList[info.minClusterIdx].total_credit_food;
                    //Redistribute money
                    for (uint j=0; j<pointList.length; j++){
                        if (pointList[j].cluster == info.minClusterIdx && pointList[j].category ==0){
                            bonus_credit = clusterList[info.minClusterIdx].total_credit_food*pointList[j].credit/total_non_food_credit;
                            payable(pointList[j].sender).transfer(bonus_credit+pointList[j].credit);
                         }
                    }
                }
            }
            else if (category==1 && info.foundCluster==0){
                //if point reports a food source position and  belongs to nothing, create new cluster
                clusterList.push(Cluster(x,y,curtime + max_life, 0, 1, amount, amount, uncertainty));
                pointList.push(Point(x,y,amount, category, clusterList.length-1, msg.sender, uncertainty));
            }
            else{
                //Do nothing and transfer back, if anything else
                payable(msg.sender).transfer(amount);
            }
        }
    }

    function getSourceList() public view returns(Cluster[] memory){
        return clusterList;
    }

    function getClusterInfo() public view returns(clusterInfo memory){
        return info;
    }
}