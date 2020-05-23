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
# AlgoNim: let's play a crypto-Nim on Algorand

## What's Nim?
[**Nim**](https://en.wikipedia.org/wiki/Nim) is a very simple mathematical game of strategy for two players. With a lot of imagination let's name them **Alice** and **Bob**.

Just to be fair from the very beginning: Nim is a **zero-sum game** and has been **"mathematically solved"**, this means that exists an **"easily calculated"** perfect strategy to determine which player will win and what winning moves are open to that player.

**So if Alice is a computer, Bob better avoid betting on winning the game.**

## What's AlgoNim?
**AlgoNim** is a cryptographic version of Nim that runs on [Algorand](https://algorand.foundation/) blockchain, so nobody can cheat. The game has been implemented using Algorand  [**Python SDK**](https://developer.algorand.org/docs/reference/sdks/#python) +  [**PyTeal**](https://github.com/algorand/pyteal). PyTeal is a binding for [**TEAL**](https://developer.algorand.org/docs/features/asc1/teal_overview/), the **stateless bytecode stack based** language for [Algorand Smart Contracts (ASC1s)](https://developer.algorand.org/docs/asc).

## AlgoNim rules
AlgoNim is based on **Nim's "normal" variant**. Alice is the player who creates the match: she has the role of **Dealer** and sets up the game table.

Rules are trivial:
1. The Dealer chooses the number **N** of pieces to put on the game table for the match;
2. The Dealer chooses the number **M** of pieces that can be removed at the most from the game table in each turn;
3. Alice and Bob choose who moves first;
4. On each turn each player removes **at least 1** and **at the most M** pieces from the game table;

**Who removes the last piece form the table wins the match!**

Alice and Bob may choose betting some ALGO for the match. Further implementations will accept **AlgoNim ASA Score Points** other then the betting reward for the matches, this will enable an **AlgoNim global ranking** too!

## AlgoNim architecture
AlgoNim architecture is composed by following Algorand features:
1. Standalone Account - Alice (acts as Dealer too)
2. Standalone Account - Bob
3. Algorand Smart Contract - Game Table
4. Algorand Smart Contract - Sink
5. Algorand Smart Contract - Alice's Bet Escrow
6. Algorand Smart Contract - Bob's Bet Escrow

### AlgoNim ASC1 - Game Table
