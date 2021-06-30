const fs = require('fs');
const solc = require('solc');
const Web3 = require('web3');
const web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));

async function deploy() {
    let accounts = await web3.eth.getAccounts();
    let password = '';
    let code = fs.readFileSync('/root/shared/Estimation.sol', 'utf8')

    var solcInput = {
	language: "Solidity",
	sources: { 
            contract: {
		content: code
            }
	},
	settings: {
            optimizer: {
		enabled: true
            },
            evmVersion: "byzantium",
            outputSelection: {
		"*": {
		    "": [
			"legacyAST",
			"ast"
		    ],
		    "*": [
			"abi",
			"evm.bytecode.object",
			"evm.bytecode.sourceMap",
			"evm.deployedBytecode.object",
			"evm.deployedBytecode.sourceMap",
			"evm.gasEstimates"
		    ]
		},
            }
	}
    };
    
    solcInput = JSON.stringify(solcInput);
    let compiledCode = solc.compile(solcInput);
    console.log(compiledCode);
    let compiledCodeJSON = JSON.parse(compiledCode);
    let abi = compiledCodeJSON.contracts.contract.Estimation.abi;
    let bytecode = compiledCodeJSON.contracts.contract.Estimation.evm.bytecode.object;

    fs.writeFileSync("/root/deployed_contract/contractABI.abi", JSON.stringify(abi));
    fs.writeFileSync("/root/deployed_contract/contractData.bin", JSON.stringify(bytecode));
    const myContract = new web3.eth.Contract(abi);
    let transactionConfig = {from: accounts[0], gas: 1500000, gasPrice: '1'}
    myContract.deploy({data: '0x' + bytecode}).send(transactionConfig).then((readyContract)=> {
    console.log(readyContract.options.address);
    fs.writeFileSync("/root/deployed_contract/contractAddress.txt", readyContract.options.address);
    }).catch(error => {
       console.log(error)
    });
}

deploy()
.then(() => console.log('Success'))
.catch(err => console.log('Script failed:', err));
