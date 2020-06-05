```
      _       __                 ____  _____   _               
     / \     [  |               |_   \|_   _| (_)              
    / _ \     | |  .--./)  .--.   |   \ | |   __   _ .--..--.  
   / ___ \    | | / /'`\;/ .'`\ \ | |\ \| |  [  | [ `.-. .-. | 
 _/ /   \ \_  | | \ \._//| \__. |_| |_\   |_  | |  | | | | | | 
|____| |____|[___].',__`  '.__.'|_____|\____|[___][___||__||__]
                 ( ( __))                                      
                                                       by cusma
```
# AlgoNim: let's play a crypto-Nim on Algorand from the CLI

## What's Nim?
[**Nim**](https://en.wikipedia.org/wiki/Nim) is a very simple mathematical game of strategy for two players. With a lot of imagination let's name them **Alice** and **Bob**.

Just to be fair from the very beginning: Nim is a **zero-sum game** and has been **"mathematically solved"**, this means that exists an **"easily calculated"** perfect strategy to determine which player will win and what winning moves are open to that player.

**So if Alice is a computer, Bob better avoid betting on winning the game.**

## What's AlgoNim?
**AlgoNim** is a cryptographic version of Nim that runs on [Algorand](https://algorand.foundation/) Layer 1, directly on the Pure Proof of Stake consensus protocol, so nobody can cheat. The game implementation takes advantage of all the features introduced in Algorand 2.0 protocol: [**Algorand Standard Assets (ASA)**](https://developer.algorand.org/docs/features/asa/), [**Atomic Transfers (AT)**](https://developer.algorand.org/docs/features/atomic_transfers/) and [**Algorand Smart Contracts (ASC1)**](Algorand Smart Contracts (ASC1)) using Algorand  [**Python SDK**](https://developer.algorand.org/docs/reference/sdks/#python) +  [**PyTeal**](https://github.com/algorand/pyteal). PyTeal is a binding for [**TEAL**](https://developer.algorand.org/docs/features/asc1/teal_overview/), the **stateless bytecode stack based** language for ASC1, in this sens AlgoNim is a truly stateless game.

Through the **seamless interaction** between Algorand Python SDK and PyTeal, AlgoNim **automatically writes** and initializes a **dedicated set of stateless TEAL ASC1s and ASAs** for each match. The whole match set-up **takes few seconds** and **costs about 0.8 ALGO**. Considerng that a new ASA + ASC1 architecture is generated for each match, **this time/cost performance is quite impressive if compared to other blockchains**.

AlgoNim is played entirely from the **command line interface**.

## AlgoNim rules
AlgoNim is based on **Nim's "normal" variant**. Alice is the player who creates the match: she is the **Dealer** and sets up the game table. Bob is yhe **Opponent**.

Rules are trivial:
1. The Dealer chooses the number **N** of pieces to put on the game table for the match;
2. The Dealer chooses the number **M** of pieces that can be removed at the most from the game table in each turn;
3. Alice and Bob choose who moves first;
4. On each turn each player removes **at least 1** and **at the most M** pieces from the game table;

**Who removes the last piece form the table wins the match!**

Alice and Bob may choose **betting** some ALGOs for the match. Further implementations will accept **AlgoNim ASA Score Points** other then the betting reward for the matches, this will enable an **AlgoNim global ranking** too!

## Install AlgoNim
### Step 1 - Python modules
AlgoRithm uses the following Python 3 modules:
1. `msgpack`
2. `docopt`
3. `algosdk`
4. `pyteal`
so you need to install them (if not already present):

```
$ pip3 install msgpack
$ pip3 install docopt
$ pip3 install algosdk
$ pip3 install pyteal
```

### Step 2 - Environment setting
To run AlgoNim smoothly you need to set the following environmental variables:
`$ export ALGORAND_DATA=/path/to/node/data`
`$ export PATH=/path/to/node/:$PATH`
Attention: setting `$ALGORAND_DATA` on your node you choose playing AlgoNim on MainNet, TestNet or BetaNet.

### Step 3 - algonim.py
Copy `algonim.py` into your `node` directory (the same of `goal`).

## How to play
Playing AlgoNim from your CLI is pretty easy, just ask for help:
**Input**
```bash
$ python3 algonim.py --help
```
**Output**
```bash
AlgoNim, the first crypto-mini-game on Algorand! (by cusma)

Usage:
  algonim.py setup <dealer_mnemonic> <opponent_address> <hours_duration>
                   [--bet-amount=<ba>] [--pieces=<ps>] [--max-removal=<mr>]
  algonim.py join <opponent_mnemonic>
  algonim.py play <player_mnemonic> <asa_pieces_amount>
  algonim.py status <player_address>
  algonim.py [--help]


Commands:
  setup    Dealer sets up a new AlgoNim match.
  join     Opponent joins the match.
  play     Play your turn.
  status   Display current match status.


Options:
  -b <ba> --bet-amount=<ba>     Set the bet amount in microAlgos
                                [default: 0].
  -p <ps> --pieces=<ps>         Set the total amount of pieces on game table
                                [default: 21].
  -m <mr> --max-removal=<mr>    Set maximum amount of pieces removal
                                [default: 4].
  -h --help
```

### Step 1 - Match set up (Dealer)
In the first step the Dealer sets up the match, generating the ASAs + ASC1s game architecture. To set up the match the Dealer may choose the following options (or left as default values otherwise):
1. `[--bet-amount=<ba>]` is the 
```bash
algonim.py setup <dealer_mnemonic> <opponent_address> <hours_duration>
                   [--bet-amount=<ba>] [--pieces=<ps>] [--max-removal=<mr>]
```
Match's data will be packed in `algonim.match` file. 

## AlgoNim architecture
AlgoNim architecture is composed by following Algorand features:
1. Standalone Account - Alice (acts as Dealer too)
2. Standalone Account - Bob
3. Algorand Smart Contract - Game Table
4. Algorand Smart Contract - Sink
5. Algorand Smart Contract - Alice's Bet Escrow
6. Algorand Smart Contract - Bob's Bet Escrow
