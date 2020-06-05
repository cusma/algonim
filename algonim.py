'''AlgoNim, the first crypto-mini-game on Algorand! (by cusma)

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

'''


import os
import json
import msgpack
from docopt import docopt
from algosdk import algod, encoding, logic, mnemonic, transaction
from pyteal import *


def create_algod_client(print_status=False, print_version=False):
    '''HELP create_algod_client:
        (boo, bool) - Returns an Algod Client and shows network status and
        version. $ALGORAND_DATA must be set as environment variable'''
    ALGORAND_DATA = os.environ.get("ALGORAND_DATA")
    if not ALGORAND_DATA:
        raise Exception("Set the environment variable $ALGORAND_DATA from the "
                        + "CLI entering: export ALGORAND_DATA=/path/to/data/")
    if not ALGORAND_DATA[-1] == "/":
        ALGORAND_DATA += "/"
    with open(ALGORAND_DATA + "algod.token", "r") as file:
        algod_token = file.read().splitlines()
        algod_token = algod_token[0]
        file.close()
    with open(ALGORAND_DATA + "algod.net", "r") as file:
        algod_address = file.read().splitlines()
        file.close()
    algod_address = 'http://' + algod_address[0]
    algod_client = algod.AlgodClient(algod_token, algod_address)

    try:
        status = algod_client.status()
        versions = algod_client.versions()
        if print_status:
            print("||-=-=-{  Algorand Network Status  }-=-=-||")
            print(json.dumps(status, indent=4))
            print("")
        if print_version:
            print("||-=-=-{  Algorand Network Version }-=-=-||")
            print(json.dumps(versions, indent=4))
            print("")
    except Exception as e:
        print(e)
    return algod_client


def wait_for_tx_confirmation(algod_client, txid):
    '''HELP wait_for_tx_confirmation:
        (class, class) - Wait for TX confirmation and displays confirmation
        round'''
    last_round = algod_client.status().get('lastRound')
    while True:
        txinfo = algod_client.pending_transaction_info(txid)
        if txinfo.get('round') and txinfo.get('round') > 0:
            print("Transaction {} confirmed in round {}.".format(
                txid, txinfo.get('round')))
            break
        else:
            print("Waiting for confirmation...")
            last_round += 1
            algod_client.status_after_block(last_round)
            
            
def unsigned_asset_send(algod_client, sender, receiver, asset_id, asa_amount,
                        validity_range=1000):
    '''HELP unsigned_asset_send:
        (AlgodClient, dict, str, int, int, int) - Returns an unsigned
        AssetTransferTxn.
    '''
    assert type(asa_amount) == int and validity_range <= 1000
    # Get network suggested params for transactions.
    params = algod_client.suggested_params()
    first_valid = params.get("lastRound")
    last_valid = first_valid + validity_range
    gh = params.get("genesishashb64")
    min_fee = params.get("minFee")
    assert min_fee <= 1000
    data = {
        "sender": sender,
        "fee": min_fee,
        "first": first_valid,
        "last": last_valid,
        "gh": gh,
        "receiver": receiver,
        "amt": asa_amount,
        "index": asset_id,
        "flat_fee": True,
        }
    return transaction.AssetTransferTxn(**data)


def unsigned_send(algod_client, addr_sender, addr_receiver, microalgo_amount,
                  validity_range=1000):
    '''HELP unsigned_send:
        (AlgodClient, str, str, int, int) - Returns an unsigned PaymentTxn.
    '''
    assert type(microalgo_amount) == int and validity_range <= 1000
    # Get network suggested params for transactions.
    params = algod_client.suggested_params()
    first_valid = params.get("lastRound")
    last_valid = first_valid + validity_range
    gh = params.get("genesishashb64")
    min_fee = params.get("minFee")
    assert min_fee <= 1000

    data = {
        "sender": addr_sender,
        "receiver": addr_receiver,
        "fee": min_fee,
        "first": first_valid,
        "last": last_valid,
        "gh": gh,
        "amt": int(microalgo_amount),
        "flat_fee": True,
        }
    return transaction.PaymentTxn(**data)


def send(algod_client, sender, addr_receiver, microalgo_amount,
         validity_range=1000):
    '''HELP send:
        (AlgodClient, dict, str, int, int) - Executes a PaymentTxn.
    '''
    assert type(microalgo_amount) == int and validity_range <= 1000
    # Get network suggested params for transactions.
    params = algod_client.suggested_params()
    first_valid = params.get("lastRound")
    last_valid = first_valid + validity_range
    gh = params.get("genesishashb64")
    min_fee = params.get("minFee")
    assert min_fee <= 1000

    data = {
        "sender": sender['pk'],
        "fee": min_fee,
        "first": first_valid,
        "last": last_valid,
        "gh": gh,
        "receiver": addr_receiver,
        "amt": int(microalgo_amount),
        "flat_fee": True
        }

    txn = transaction.PaymentTxn(**data)
    stxn = txn.sign(sender['sk'])
    txid = algod_client.send_transaction(stxn)
    print("Transaction ID:", txid)
    wait_for_tx_confirmation(algod_client, txid)


def unsigned_closeto(algod_client, sender, closeto, validity_range=1000):
    '''HELP unsigned_closeto:
        (AlgodClient, dict, str, int) - Closes an Account.
    '''
    # Get network suggested params for transactions.
    assert validity_range <= 1000
    params = algod_client.suggested_params()
    first_valid = params.get("lastRound")
    last_valid = first_valid + validity_range
    gh = params.get("genesishashb64")
    min_fee = params.get("minFee")
    assert min_fee <= 1000

    data = {
        "sender": sender,
        "receiver": closeto,
        "fee": min_fee,
        "first": first_valid,
        "last": last_valid,
        "gh": gh,
        "amt": 0,
        "flat_fee": True,
        "close_remainder_to": closeto
        }
    return transaction.PaymentTxn(**data)


def asa_pieces_create(algod_client,
                      asset_creator,
                      total):
    '''HELP asa_pieces_create:
        (AlgodClient, str, int) - Returns AlgoNim ASA Pieces Asset ID
    '''
    assert type(total) == int
    # Get network suggested params for transactions.
    params = algod_client.suggested_params()
    first_valid = params.get("lastRound")
    last_valid = first_valid + 1000
    gh = params.get("genesishashb64")
    min_fee = params.get("minFee")
    assert min_fee <= 1000

    data = {
        "sender": asset_creator['pk'],
        "fee": min_fee,
        "first": first_valid,
        "last": last_valid,
        "gh": gh,
        "total": total,
        "default_frozen": False,
        "unit_name": 'ALGONIMP',
        "asset_name": 'AlgoNim Piece',
        "manager": asset_creator['pk'],
        "reserve": asset_creator['pk'],
        "freeze": '',
        "clawback": '',
        "url": 'https://github.com/cusma/algonim',
        "flat_fee": True,
        "strict_empty_address_check": False,
        "decimals": 0
        }

    txn = transaction.AssetConfigTxn(**data)
    stxn = txn.sign(asset_creator['sk'])
    txid = algod_client.send_transaction(stxn)
    print("Transaction ID:", txid)
    wait_for_tx_confirmation(algod_client, txid)

    try:
        # Pull account info for the asset creator
        account_info = algod_client.account_info(asset_creator['pk'])
        # Get max asset ID
        asa_pieces_id = max(
            map(lambda x: int(x), account_info.get('thisassettotal').keys()))
        print("AlgoNim ASA Piece ID: {}".format(asa_pieces_id))
        print(json.dumps(
            account_info['thisassettotal'][str(asa_pieces_id)],
            indent=4))
    except Exception as e:
        print(e)
    return asa_pieces_id


def asa_turn_create(algod_client,
                    asset_creator):
    '''HELP asa_turn_create:
        (AlgodClient, str) - Returns AlgoNim ASA Turn Asset ID
    '''
    # Get network suggested params for transactions.
    params = algod_client.suggested_params()
    first_valid = params.get("lastRound")
    last_valid = first_valid + 1000
    gh = params.get("genesishashb64")
    min_fee = params.get("minFee")
    assert min_fee <= 1000

    data = {
        "sender": asset_creator['pk'],
        "fee": min_fee,
        "first": first_valid,
        "last": last_valid,
        "gh": gh,
        "total": 1,
        "default_frozen": False,
        "unit_name": 'ALGONIMT',
        "asset_name": 'AlgoNim Turn',
        "manager": asset_creator['pk'],
        "reserve": asset_creator['pk'],
        "freeze": '',
        "clawback": '',
        "url": 'https://github.com/cusma/algonim',
        "flat_fee": True,
        "strict_empty_address_check": False,
        "decimals": 0
        }

    txn = transaction.AssetConfigTxn(**data)
    stxn = txn.sign(asset_creator['sk'])
    txid = algod_client.send_transaction(stxn)
    print("Transaction ID:", txid)
    wait_for_tx_confirmation(algod_client, txid)

    try:
        # Pull account info for the asset creator
        account_info = algod_client.account_info(asset_creator['pk'])
        # Get max asset ID
        asa_turn_id = max(
            map(lambda x: int(x), account_info.get('thisassettotal').keys()))
        print("AlgoNim ASA Turn: {}".format(asa_turn_id))
        print(json.dumps(
            account_info['thisassettotal'][str(asa_turn_id)],
            indent=4))
    except Exception as e:
        print(e)
    return asa_turn_id


def asa_score_create(algod_client,
                     asset_creator):
    '''HELP asa_score_create:
        (AlgodClient, str) - Returns AlgoNim ASA Score Asset ID
    '''
    # Get network suggested params for transactions.
    params = algod_client.suggested_params()
    first_valid = params.get("lastRound")
    last_valid = first_valid + 1000
    gh = params.get("genesishashb64")
    min_fee = params.get("minFee")
    assert min_fee <= 1000

    data = {
        "sender": asset_creator['pk'],
        "fee": min_fee,
        "first": first_valid,
        "last": last_valid,
        "gh": gh,
        "total": 1,
        "default_frozen": False,
        "unit_name": 'ALGONIMS',
        "asset_name": 'AlgoNim Score',
        "manager": asset_creator['pk'],
        "reserve": asset_creator['pk'],
        "freeze": '',
        "clawback": '',
        "url": 'https://github.com/cusma/algonim',
        "flat_fee": True,
        "strict_empty_address_check": False,
        "decimals": 0
        }

    txn = transaction.AssetConfigTxn(**data)
    stxn = txn.sign(asset_creator['sk'])
    txid = algod_client.send_transaction(stxn)
    print("Transaction ID:", txid)
    wait_for_tx_confirmation(algod_client, txid)

    try:
        # Pull account info for the asset creator
        account_info = algod_client.account_info(asset_creator['pk'])
        # Get max asset ID
        asa_score_id = max(
            map(lambda x: int(x), account_info.get('thisassettotal').keys()))
        print("AlgoNim ASA Turn: {}".format(asa_score_id))
        print(json.dumps(
            account_info['thisassettotal'][str(asa_score_id)],
            indent=4))
    except Exception as e:
        print(e)
    return asa_score_id


def bet_atomic_transfer(algod_client, dealer, addr_opponent,
                        addr_dealer_bet_escrow, addr_opponent_bet_escrow,
                        microalgo_bet_amount):
    '''HELP bet_atomic_transfer:
        (AlgodClient, dict, str, str, str, int) - Returns Bet Atomic Transfer
        partially signed by the Dealer, to be signed by the Opponent.
    '''

    dealer_bet_txn = unsigned_send(algod_client, dealer['pk'],
                                   addr_dealer_bet_escrow,
                                   microalgo_bet_amount)
    opponent_bet_txn = unsigned_send(algod_client, addr_opponent,
                                     addr_opponent_bet_escrow,
                                     microalgo_bet_amount)

    # Gorup Transaction
    gid = transaction.calculate_group_id([dealer_bet_txn, opponent_bet_txn])
    dealer_bet_txn.group = gid
    opponent_bet_txn.group = gid

    dealer_bet_stxn = dealer_bet_txn.sign(dealer['sk'])
    return dealer_bet_stxn, opponent_bet_txn


def asc1_sink_teal(asa_pieces_id,
                   asa_pieces_total,
                   player_alice,
                   player_bob):
    '''HELP asc1_sink_teal:
        (int, int, str, str) - Returns AlgoNim ASC1 Sink raw TEAL
    '''
    # AlgoNim ASC1 Sink controls the following conditions:
    # 1. AlgoNim ASA Pieces Opt-In
    # 2. Empty Sink: Alice or Bob remove all the AlgoNim ASA Pieces total
    # supply from the Sink as winning proof.
    asa_pieces_id = Int(asa_pieces_id)
    asa_pieces_total = Int(asa_pieces_total)
    addr_alice = Addr(player_alice)
    addr_bob = Addr(player_bob)

    # ASC1 Constants:
    tmpl_fee = Int(1000)

    # ASC1 Logic:
    # 1. AlgoNim ASA Pieces Opt-In
    asa_pieces_opt_in = And(Txn.type_enum() == Int(4),
                            Txn.fee() <= tmpl_fee,
                            Txn.xfer_asset() == asa_pieces_id,
                            Txn.asset_amount() == Int(0))

    # 2. Empty Sink
    empty_sink_alice = And(Txn.group_index() == Int(2),
                           Txn.type_enum() == Int(4),
                           Txn.fee() <= tmpl_fee,
                           Txn.xfer_asset() == asa_pieces_id,
                           Txn.asset_amount() == asa_pieces_total,
                           Txn.asset_receiver() == addr_alice)

    empty_sink_bob = And(Txn.group_index() == Int(2),
                         Txn.type_enum() == Int(4),
                         Txn.fee() <= tmpl_fee,
                         Txn.xfer_asset() == asa_pieces_id,
                         Txn.asset_amount() == asa_pieces_total,
                         Txn.asset_receiver() == addr_bob)

    empty_sink = Or(empty_sink_alice, empty_sink_bob)
    return Or(asa_pieces_opt_in, empty_sink)


def asc1_game_table_teal(asa_pieces_id,
                         asa_pieces_total,
                         asa_pieces_max_remove,
                         asa_turn_id,
                         player_alice,
                         player_bob,
                         sink):
    '''HELP asc1_game_table_teal:
        (int, int, int, int, str, str, str) - Returns AlgoNim ASC1 Game Table
        raw TEAL
    '''
    # AlgoNim ASC1 Game Table controls the following conditions:
    # 1. Dealer - Funding Game Table with AlgoNim ASA Pieces
    # 2. Play Turn - Player correctly removes ASA Pieces from the Game Table
    asa_pieces_id = Int(asa_pieces_id)
    asa_pieces_total = Int(asa_pieces_total)
    asa_pieces_max_remove = Int(asa_pieces_max_remove)
    asa_turn_id = Int(asa_turn_id)
    addr_alice = Addr(player_alice)
    addr_bob = Addr(player_bob)
    addr_sink = Addr(sink)

    # ASC1 Constants:
    tmpl_fee = Int(1000)

    # ASC1 Logic:
    # 1. Dealer
    asa_pieces_opt_in = And(Gtxn.type_enum(0) == Int(4),
                            Gtxn.fee(0) <= tmpl_fee,
                            Gtxn.xfer_asset(0) == asa_pieces_id,
                            Gtxn.asset_amount(0) == Int(0))

    game_table_setup = And(Gtxn.type_enum(1) == Int(4),
                           Gtxn.fee(1) <= tmpl_fee,
                           Gtxn.xfer_asset(1) == asa_pieces_id,
                           Gtxn.asset_amount(1) == asa_pieces_total,
                           Gtxn.sender(1) == addr_alice)

    dealer = And(asa_pieces_opt_in, game_table_setup)

    # 2. Play Turn
    change_turn_alice_to_bob = And(Gtxn.type_enum(0) == Int(4),
                                   Gtxn.fee(0) <= tmpl_fee,
                                   Gtxn.xfer_asset(0) == asa_turn_id,
                                   Gtxn.asset_amount(0) == Int(1),
                                   Gtxn.sender(0) == addr_alice,
                                   Gtxn.asset_receiver(0) == addr_bob)

    change_turn_bob_to_alice = And(Gtxn.type_enum(0) == Int(4),
                                   Gtxn.fee(0) <= tmpl_fee,
                                   Gtxn.xfer_asset(0) == asa_turn_id,
                                   Gtxn.asset_amount(0) == Int(1),
                                   Gtxn.sender(0) == addr_bob,
                                   Gtxn.asset_receiver(0) == addr_alice)

    change_turn = Or(change_turn_alice_to_bob, change_turn_bob_to_alice)

    remove_asa_pieces = And(Gtxn.type_enum(1) == Int(4),
                            Gtxn.fee(1) <= tmpl_fee,
                            Gtxn.xfer_asset(1) == asa_pieces_id,
                            Gtxn.asset_amount(1) >= Int(1),
                            Gtxn.asset_amount(1) <= asa_pieces_max_remove,
                            Gtxn.asset_receiver(1) == addr_sink)

    play_turn = And(change_turn, remove_asa_pieces)
    return Or(dealer, play_turn)


def asc1_bet_escrow_teal(algod_client,
                         asa_pieces_id,
                         asa_pieces_total,
                         asa_turn_id,
                         addr_escrow_owner,
                         addr_adversary_player,
                         sink,
                         game_table,
                         match_hours_timeout):
    '''HELP asc1_sink_raw_teal:
        (...) - Returns AlgoNim ASC1 Bet Escrow raw TEAL
    '''
    # AlgoNim Bet Escrow controls the following conditions:
    # 1. Opponent wins
    # 2. Bet escrow expires
    asa_pieces_id = Int(asa_pieces_id)
    asa_pieces_total = Int(asa_pieces_total)
    asa_turn_id = Int(asa_turn_id)
    addr_owner = Addr(addr_escrow_owner)
    addr_adversary = Addr(addr_adversary_player)
    addr_sink = Addr(sink)
    addr_game_table = Addr(game_table)

    # Blockchain Parameters
    blockchain_params = algod_client.suggested_params()
    first_valid = blockchain_params.get("lastRound")

    # AlgoNim Bet Escrow expiration
    match_blocks_duration = int(match_hours_timeout * 3600 // 5)
    print("AlgoNim Bet Escrows Expiry block:",
          first_valid + match_blocks_duration)
    bet_escrow_expiry_block = Int(first_valid + match_blocks_duration)

    # ASC1 Constants:
    tmpl_fee = Int(1000)

    # ASC1 Logic:
    # 1. Opponent wins
    change_turn = And(Gtxn.type_enum(0) == Int(4),
                      Gtxn.fee(0) <= tmpl_fee,
                      Gtxn.xfer_asset(0) == asa_turn_id,
                      Gtxn.asset_amount(0) == Int(1),
                      Gtxn.sender(0) == addr_adversary,
                      Gtxn.asset_receiver(0) == addr_owner)

    last_move = And(Gtxn.type_enum(1) == Int(4),
                    Gtxn.fee(1) <= tmpl_fee,
                    Gtxn.xfer_asset(1) == asa_pieces_id,
                    Gtxn.sender(1) == addr_game_table,
                    Gtxn.asset_receiver(1) == addr_sink)

    winner_proof = And(Gtxn.type_enum(2) == Int(4),
                       Gtxn.fee(2) <= tmpl_fee,
                       Gtxn.xfer_asset(2) == asa_pieces_id,
                       Gtxn.sender(2) == addr_sink,
                       Gtxn.asset_receiver(2) == addr_adversary,
                       Gtxn.asset_amount(2) == asa_pieces_total)

    collect_reward = And(Gtxn.type_enum(3) == Int(1),
                         Gtxn.fee(3) <= tmpl_fee,
                         Gtxn.receiver(3) == addr_adversary,
                         Gtxn.amount(3) == Int(0),
                         Gtxn.close_remainder_to(3) == addr_adversary)

    win = And(change_turn, last_move, winner_proof, collect_reward)

    # 2. Bet Escrow Timeout
    bet_escrow_timeout = And(Txn.type_enum() == Int(1),
                             Txn.fee() <= tmpl_fee,
                             Txn.receiver() == Global.zero_address(),
                             Txn.amount() == Int(0),
                             Txn.close_remainder_to() == addr_adversary,
                             Txn.first_valid() > bet_escrow_expiry_block)
    return Or(win, bet_escrow_timeout)


def compile_raw_teal(asc1_source, new_asc1_fname):
    '''HELP compile_raw_teal:
        (PyTealObj, str, str, str) - Returns ASC1 Contract Account and
        LogicSig. GOAL must be in your PATH, if not so from the CLI enter:
        export PATH=/path/to/node:$PATH
    '''

    asc1_teal_fname = new_asc1_fname + ".teal"
    with open(asc1_teal_fname, "w+") as f:
        f.write(asc1_source.teal())
    asc1_tealc_fname = new_asc1_fname + ".tealc"
    stdout, stderr = execute(["goal", "clerk", "compile", "-o",
                              asc1_tealc_fname, asc1_teal_fname])
    if stderr != "":
        print(stderr)
        raise
    elif len(stdout) < 59:
        print("Error in compile TEAL")
        raise

    with open(asc1_tealc_fname, "rb") as f:
        asc1_bytes = f.read()
    asc1_lsig = transaction.LogicSig(asc1_bytes)
    addr_asc1 = logic.address(asc1_bytes)
    return asc1_lsig, addr_asc1


def play_last_turn(algod_client, player, addr_adversary,
                   addr_game_table, game_table_lsig,
                   addr_sink, sink_lsig,
                   addr_adversary_bet_escrow, adversary_bet_escrow_lsig,
                   asa_turn_id, asa_pieces_id,
                   asa_pieces_total, asa_pieces_amount):
    '''HELP play_last_turn:
        (AlgodClient, dict, str, str, str, str, str,  str, str, int, int, int,
        int) - Play last turn moving ASA Pieces form the Game Table to the Sink
        and show the winning proof to the opponent's Bet Escrow.
    '''

    txn0 = unsigned_asset_send(algod_client, player['pk'], addr_adversary,
                               asa_turn_id, 1)
    txn1 = unsigned_asset_send(algod_client, addr_game_table, addr_sink,
                               asa_pieces_id, asa_pieces_amount)
    txn2 = unsigned_asset_send(algod_client, addr_sink, player['pk'],
                               asa_pieces_id, asa_pieces_total)
    txn3 = unsigned_closeto(algod_client, addr_adversary_bet_escrow,
                            player['pk'])

    # Gorup Transaction
    gid = transaction.calculate_group_id([txn0, txn1, txn2, txn3])
    txn0.group = gid
    txn1.group = gid
    txn2.group = gid
    txn3.group = gid

    stxn0 = txn0.sign(player['sk'])
    lstxn1 = transaction.LogicSigTransaction(txn1, game_table_lsig)
    lstxn2 = transaction.LogicSigTransaction(txn2, sink_lsig)
    lstxn3 = transaction.LogicSigTransaction(txn3, adversary_bet_escrow_lsig)

    sgtxn = []
    sgtxn.append(stxn0)
    sgtxn.append(lstxn1)
    sgtxn.append(lstxn2)
    sgtxn.append(lstxn3)
    txid = algod_client.send_transactions(sgtxn)
    print("\nI WON !!! Arrivederci " + addr_adversary)
    print("Transaction ID: ", txid)
    wait_for_tx_confirmation(algod_client, txid)


def play_turn(algod_client, player, addr_adversary,
              addr_game_table, game_table_lsig,
              addr_sink, sink_lsig,
              addr_adversary_bet_escrow, adversary_bet_escrow_lsig,
              asa_turn_id, asa_pieces_id,
              asa_pieces_total, asa_pieces_max_remove, asa_pieces_amount):
    '''HELP play_turn:
        (AlgodClient, dict, str, str, str, str, str,  str, str, int, int, int,
        int, int) - Play turn moving ASA Pieces form the Game Table to the Sink
    '''

    game_table_info = algod_client.account_info(addr_game_table)

    pieces_on_table = game_table_info['assets'][str(asa_pieces_id)]['amount']

    if pieces_on_table > asa_pieces_max_remove:
        txn0 = unsigned_asset_send(algod_client, player['pk'], addr_adversary,
                                   asa_turn_id, 1)
        txn1 = unsigned_asset_send(algod_client, addr_game_table, addr_sink,
                                   asa_pieces_id, asa_pieces_amount)

        # Gorup Transaction
        gid = transaction.calculate_group_id([txn0, txn1])
        txn0.group = gid
        txn1.group = gid
        stxn0 = txn0.sign(player['sk'])
        lstxn1 = transaction.LogicSigTransaction(txn1, game_table_lsig)
        sgtxn = []
        sgtxn.append(stxn0)
        sgtxn.append(lstxn1)
        txid = algod_client.send_transactions(sgtxn)
        print("\nRemoving", asa_pieces_amount, "pieces from the Game table...")
        print("Transaction ID: ", txid)
        wait_for_tx_confirmation(algod_client, txid)
    else:
        play_last_turn(algod_client, player, addr_adversary,
                       addr_game_table, game_table_lsig,
                       addr_sink, sink_lsig,
                       addr_adversary_bet_escrow, adversary_bet_escrow_lsig,
                       asa_turn_id, asa_pieces_id,
                       asa_pieces_total, asa_pieces_amount)


def match_setup(algod_client, dealer_passphrase, addr_opponent,
                match_hours_timeout, microalgo_bet_amount, asa_pieces_total,
                asa_pieces_max_remove):
    '''HELP match_setup:
        (AlgodClient, str, str, float, int, int, int) - Sets up a new AlgoNim
        match
    '''

    # AlgoNim Players
    # Palyer 1 (Dealer) - Match Set Up costs about: 0.8 ALGO
    dealer = {}
    dealer['pk'] = mnemonic.to_public_key(dealer_passphrase)
    dealer['sk'] = mnemonic.to_private_key(dealer_passphrase)

    # Player 2 (Opponent) - Must Opt-In AlgoNim ASAs to play the match
    opponent = {}
    opponent['pk'] = addr_opponent

    print("                                                               ")
    print("      _       __                 ____  _____   _               ")
    print("     / \     [  |               |_   \|_   _| (_)              ")
    print("    / _ \     | |  .--./)  .--.   |   \ | |   __   _ .--..--.  ")
    print("   / ___ \    | | / /'`\;/ .'`\ \ | |\ \| |  [  | [ `.-. .-. | ")
    print(" _/ /   \ \_  | | \ \._//| \__. |_| |_\   |_  | |  | | | | | | ")
    print("|____| |____|[___].',__`  '.__.'|_____|\____|[___][___||__||__]")
    print("                 ( ( __))                                      ")
    print("                                                       by cusma")
    print("                                                               ")
    print("  Welcome to AlgoNim, the first crypto-mini-game on Algorand!  ")

    # Asset Create: AlgoNim ASA Pieces
    print("")
    print("Dealer creating AlgoNim ASA Piece for this match...")
    asa_pieces_id = asa_pieces_create(algod_client, dealer, asa_pieces_total)

    # Asset Create: AlgoNim ASA Turn
    print("")
    print("Dealer creating AlgoNim ASA Turn for this match...")
    asa_turn_id = asa_turn_create(algod_client, dealer)

    # TEAL: AlgoNim ASC1 Sink
    print("")
    print("Dealer writing AlgoNim ASC1 Sink TEAL for this match...")
    asc1_sink_source = asc1_sink_teal(
        asa_pieces_id, asa_pieces_total, dealer['pk'], opponent['pk'])

    sink_lsig, addr_sink = compile_raw_teal(asc1_sink_source,
                                            "algonim_asc1_sink")

    # Initialize AlgoNim ASC1 Sink Account with ALGO
    print("")
    print("Initializing Sink Account...")
    send(algod_client, dealer, addr_sink, 300000)

    # AlgoNim ASC1 Sink Account Opt-In
    print("")
    print("Sink Account AlgoNim ASA Piece Opt-In...")
    sink_opt_in_txn = unsigned_asset_send(
        algod_client, addr_sink, addr_sink, asa_pieces_id, 0)

    sink_opt_in_lstxn = transaction.LogicSigTransaction(
        sink_opt_in_txn, sink_lsig)

    txid = algod_client.send_transactions([sink_opt_in_lstxn])
    print("Transaction ID:", txid)
    wait_for_tx_confirmation(algod_client, txid)

    # TEAL: AlgoNim ASC1 Game Table
    print("")
    print("Dealer writing AlgoNim ASC1 Game Table TEAL for this match...")
    asc1_game_table_source = asc1_game_table_teal(
        asa_pieces_id, asa_pieces_total, asa_pieces_max_remove, asa_turn_id,
        dealer['pk'], opponent['pk'], addr_sink)

    game_table_lsig, addr_game_table = compile_raw_teal(
        asc1_game_table_source, "algonim_asc1_game_table")

    # Initialize AlgoNim ASC1 Game Table Account with ALGO
    print("")
    print("Initializing Game Table Account...")
    send(algod_client, dealer, addr_game_table, 300000)

    # Dealer Sets Up the Game Table with AlgoNim ASA Pieces
    print("")
    print("Dealer distributing ASA Pieces on the Game Table...")
    gt_opt_in_txn = unsigned_asset_send(
        algod_client, addr_game_table, addr_game_table, asa_pieces_id, 0)

    deal_pieces_txn = unsigned_asset_send(
        algod_client, dealer['pk'], addr_game_table, asa_pieces_id,
        asa_pieces_total)

    # Dealer Gorup Transaction
    dealer_gid = transaction.calculate_group_id([gt_opt_in_txn,
                                                 deal_pieces_txn])
    gt_opt_in_txn.group = dealer_gid
    deal_pieces_txn.group = dealer_gid
    gt_opt_in_lstxn = transaction.LogicSigTransaction(gt_opt_in_txn,
                                                      game_table_lsig)
    deal_pieces_stxn = deal_pieces_txn.sign(dealer['sk'])
    dealer_sgtxn = []
    dealer_sgtxn.append(gt_opt_in_lstxn)
    dealer_sgtxn.append(deal_pieces_stxn)
    txid = algod_client.send_transactions(dealer_sgtxn)
    print("Transaction ID: ", txid)
    wait_for_tx_confirmation(algod_client, txid)

    # TEAL: AlgoNim ASC1 Bet Escrow
    print("")
    print("Dealer writing AlgoNim ASC1 Bet Escrow TEAL for Palyer 1...")
    asc1_dealer_bet_escrow_source = asc1_bet_escrow_teal(
        algod_client, asa_pieces_id, asa_pieces_total, asa_turn_id,
        dealer['pk'], opponent['pk'], addr_sink, addr_game_table,
        match_hours_timeout)

    dealer_bet_escrow_lsig, addr_dealer_bet_escrow = compile_raw_teal(
        asc1_dealer_bet_escrow_source, "algonim_asc1_dealer_bet_escrow")

    print("")
    print("Dealer writing AlgoNim ASC1 Bet Escrow TEAL for Palyer 2...")
    asc1_opponent_bet_escrow_source = asc1_bet_escrow_teal(
        algod_client, asa_pieces_id, asa_pieces_total, asa_turn_id,
        opponent['pk'], dealer['pk'], addr_sink, addr_game_table,
        match_hours_timeout)

    opponent_bet_escrow_lsig, addr_opponent_bet_escrow = compile_raw_teal(
        asc1_opponent_bet_escrow_source, "algonim_asc1_opponent_bet_escrow")

    # Initialize AlgoNim ASC1 Escrows with 0.1 ALGO
    print("")
    print("Initializing Bet Escrow Accounts...")
    send(algod_client, dealer, addr_dealer_bet_escrow, 100000)
    send(algod_client, dealer, addr_opponent_bet_escrow, 100000)

    # Creating Bet Atomic Transfer to be signed by the Opponent
    dealer_bet_stxn, opponent_bet_txn = bet_atomic_transfer(
        algod_client, dealer, opponent['pk'], addr_dealer_bet_escrow,
        addr_opponent_bet_escrow, microalgo_bet_amount)

    match_data = {}
    match_data['dealer'] = dealer['pk']
    match_data['opponent'] = opponent['pk']
    match_data['asa_pieces_id'] = asa_pieces_id
    match_data['asa_pieces_total'] = asa_pieces_total
    match_data['asa_pieces_max_remove'] = asa_pieces_max_remove
    match_data['asa_turn_id'] = asa_turn_id
    match_data['sink'] = addr_sink
    match_data['sink_lsig'] = encoding.msgpack_encode(sink_lsig)
    match_data['game_table'] = addr_game_table
    match_data['game_table_lsig'] = encoding.msgpack_encode(game_table_lsig)
    match_data['dealer_bet_escrow'] = addr_dealer_bet_escrow
    match_data['dealer_bet_escrow_lsig'] = encoding.msgpack_encode(
        dealer_bet_escrow_lsig)
    match_data['opponent_bet_escrow'] = addr_opponent_bet_escrow
    match_data['opponent_bet_escrow_lsig'] = encoding.msgpack_encode(
        opponent_bet_escrow_lsig)
    match_data['dealer_bet_stxn'] = encoding.msgpack_encode(dealer_bet_stxn)
    match_data['opponent_bet_txn'] = encoding.msgpack_encode(opponent_bet_txn)
    match_data['microalgo_bet_amount'] = microalgo_bet_amount
    match_data['match_hours_timeout'] = match_hours_timeout
    match_data_bytes = msgpack.packb(match_data)
    match_data_fname = 'algonim.match'

    with open(match_data_fname, "wb") as f:
        f.write(match_data_bytes)
        f.close()

    print("                                ")
    print("              _       _         ")
    print("  /\/\   __ _| |_ ___| |__    _ ")
    print(" /    \ / _` | __/ __| '_ \  (_)")
    print("/ /\/\ \ (_| | || (__| | | |  _ ")
    print("\/    \/\__,_|\__\___|_| |_| (_)")
    print("                                ")
    print("MATCH DURATION:\t\t", match_data['match_hours_timeout'] * 60, "min")
    print("PIECES ON GAME TABLE:\t", match_data['asa_pieces_total'], "\n")
    print("RULES:")
    print("1. Players on each turn must remove at least 1 ASA Piece")
    print("2. Players on each turn must remove at most",
          match_data['asa_pieces_max_remove'], "ASA Piece")
    print("3. Who removes the last ASA Piece form the Game Table wins the "
          + "match!\n")
    print("Player 1 - Dealer:\t" + match_data['dealer'])
    print("Player 2 - Opponent:\t" + match_data['opponent'], "\n")
    print("AlgoNim ASA Pieces ID:\t", match_data['asa_pieces_id'])
    print("AlgoNim ASA Turn ID:\t", match_data['asa_turn_id'], "\n")
    print("AlgoNim Sink Account:\t\t\t" + match_data['sink'])
    print("AlgoNim Game Table Account:\t\t" + match_data['game_table'])
    print("AlgoNim Bet Escrow Player 1 Account:\t"
          + match_data['dealer_bet_escrow'])
    print("AlgoNim Bet Escrow Player 2 Account:\t"
          + match_data['opponent_bet_escrow'])
    print("\nMay the best win!\n")


# AlgoNim CLI:
args = docopt(__doc__)

algod_client = create_algod_client()

if args['setup']:
    dealer_passphrase = args['<dealer_mnemonic>']
    addr_opponent = args['<opponent_address>']
    match_hours_timeout = float(args['<hours_duration>'])
    microalgo_bet_amount = int(args['--bet-amount'])
    asa_pieces_total = int(args['--pieces'])
    asa_pieces_max_remove = int(args['--max-removal'])
    assert microalgo_bet_amount >= 0
    assert asa_pieces_total > asa_pieces_max_remove + 1
    match_setup(algod_client, dealer_passphrase, addr_opponent,
                match_hours_timeout, microalgo_bet_amount, asa_pieces_total,
                asa_pieces_max_remove)

if args['join']:
    with open("algonim.match", "rb") as f:
        match_data_bytes = f.read()
        f.close()
    match_data = msgpack.unpackb(match_data_bytes)

    opponent = {}
    opponent['pk'] = mnemonic.to_public_key(args['<opponent_mnemonic>'])
    opponent['sk'] = mnemonic.to_private_key(args['<opponent_mnemonic>'])
    microalgo_bet_amount = match_data['microalgo_bet_amount']

    # AlgoNim ASAs Opt-In
    asa_pieces_opt_in_txn = unsigned_asset_send(
        algod_client, opponent['pk'], opponent['pk'],
        match_data['asa_pieces_id'], 0)

    asa_pieces_opt_in_stxn = asa_pieces_opt_in_txn.sign(opponent['sk'])
    txid = algod_client.send_transactions([asa_pieces_opt_in_stxn])

    print("                                                               ")
    print("      _       __                 ____  _____   _               ")
    print("     / \     [  |               |_   \|_   _| (_)              ")
    print("    / _ \     | |  .--./)  .--.   |   \ | |   __   _ .--..--.  ")
    print("   / ___ \    | | / /'`\;/ .'`\ \ | |\ \| |  [  | [ `.-. .-. | ")
    print(" _/ /   \ \_  | | \ \._//| \__. |_| |_\   |_  | |  | | | | | | ")
    print("|____| |____|[___].',__`  '.__.'|_____|\____|[___][___||__||__]")
    print("                 ( ( __))                                      ")
    print("                                                       by cusma")
    print("                                                               ")
    print("  Welcome to AlgoNim, the first crypto-mini-game on Algorand!  ")
    print("")
    print("The Dealer wants to bet", microalgo_bet_amount * 10 ** -6, "ALGO.")
    join = input("Do you want to join the match? [y/N]")
    if join == 'y':
        print("\nAlgoNim ASA Piece Opt-In...")
        print("Transaction ID:", txid)
        wait_for_tx_confirmation(algod_client, txid)

        asa_turn_opt_in_txn = unsigned_asset_send(
            algod_client, opponent['pk'], opponent['pk'],
            match_data['asa_turn_id'], 0)

        asa_turn_opt_in_stxn = asa_turn_opt_in_txn.sign(opponent['sk'])

        txid = algod_client.send_transactions([asa_turn_opt_in_stxn])
        print("\nAlgoNim ASA Turn Opt-In...")
        print("Transaction ID:", txid)
        wait_for_tx_confirmation(algod_client, txid)

        # AlgoNim Players' Bet Atomic Transfer
        dealer_bet_stxn = encoding.msgpack_decode(
            match_data['dealer_bet_stxn'])
        opponent_bet_txn = encoding.msgpack_decode(
            match_data['opponent_bet_txn'])
        opponent_bet_stxn = opponent_bet_txn.sign(opponent['sk'])
        bet_sgtxn = []
        bet_sgtxn.append(dealer_bet_stxn)
        bet_sgtxn.append(opponent_bet_stxn)
        txid = algod_client.send_transactions(bet_sgtxn)
        print("\nPlayers betting...")
        print("Transaction ID = ", txid)
        wait_for_tx_confirmation(algod_client, txid)
        print("                                ")
        print("              _       _         ")
        print("  /\/\   __ _| |_ ___| |__    _ ")
        print(" /    \ / _` | __/ __| '_ \  (_)")
        print("/ /\/\ \ (_| | || (__| | | |  _ ")
        print("\/    \/\__,_|\__\___|_| |_| (_)")
        print("                                ")
        print("MATCH DURATION:\t\t", match_data['match_hours_timeout'] * 60, "min")
        print("PIECES ON GAME TABLE:\t", match_data['asa_pieces_total'], "\n")
        print("RULES:")
        print("1. Players on each turn must remove at least 1 ASA Piece")
        print("2. Players on each turn must remove at most",
              match_data['asa_pieces_max_remove'], "ASA Piece")
        print("3. Who removes the last ASA Piece form the Game Table wins the "
              + "match!\n")
        print("Player 1 - Dealer:\t" + match_data['dealer'])
        print("Player 2 - Opponent:\t" + match_data['opponent'], "\n")
        print("AlgoNim ASA Pieces ID:\t", match_data['asa_pieces_id'])
        print("AlgoNim ASA Turn ID:\t", match_data['asa_turn_id'], "\n")
        print("AlgoNim Sink Account:\t\t\t" + match_data['sink'])
        print("AlgoNim Game Table Account:\t\t" + match_data['game_table'])
        print("AlgoNim Bet Escrow Player 1 Account:\t"
              + match_data['dealer_bet_escrow'])
        print("AlgoNim Bet Escrow Player 2 Account:\t"
              + match_data['opponent_bet_escrow'])
        print("\nMay the best win!\n")
    else:
        print("See you for the next AlgoNim match! Arrivederci!")

if args['play']:
    with open("algonim.match", "rb") as f:
        match_data_bytes = f.read()
        f.close()
    match_data = msgpack.unpackb(match_data_bytes)
    player = {}
    player['pk'] = mnemonic.to_public_key(args['<player_mnemonic>'])
    player['sk'] = mnemonic.to_private_key(args['<player_mnemonic>'])
    asa_pieces_amount = int(args['<asa_pieces_amount>'])

    asa_pieces_id = match_data['asa_pieces_id']
    asa_pieces_total = match_data['asa_pieces_total']
    asa_pieces_max_remove = match_data['asa_pieces_max_remove']
    asa_turn_id = match_data['asa_turn_id']
    addr_sink = match_data['sink']
    sink_lsig = encoding.msgpack_decode(match_data['sink_lsig'])
    addr_game_table = match_data['game_table']
    game_table_lsig = encoding.msgpack_decode(match_data['game_table_lsig'])
    addr_dealer_bet_escrow = match_data['dealer_bet_escrow']
    dealer_bet_escrow_lsig = encoding.msgpack_decode(
        match_data['dealer_bet_escrow_lsig'])

    if player['pk'] == match_data['dealer']:
        addr_adversary = match_data['opponent']
        addr_adversary_bet_escrow = match_data['opponent_bet_escrow']
        adversary_bet_escrow_lsig = encoding.msgpack_decode(
            match_data['opponent_bet_escrow_lsig'])
        play_turn(algod_client, player, addr_adversary,
                  addr_game_table, game_table_lsig,
                  addr_sink, sink_lsig,
                  addr_adversary_bet_escrow, adversary_bet_escrow_lsig,
                  asa_turn_id, asa_pieces_id,
                  asa_pieces_total, asa_pieces_max_remove, asa_pieces_amount)
    else:
        addr_adversary = match_data['dealer']
        addr_adversary_bet_escrow = match_data['dealer_bet_escrow']
        adversary_bet_escrow_lsig = encoding.msgpack_decode(
            match_data['dealer_bet_escrow_lsig'])
        play_turn(algod_client, player, addr_adversary,
                  addr_game_table, game_table_lsig,
                  addr_sink, sink_lsig,
                  addr_adversary_bet_escrow, adversary_bet_escrow_lsig,
                  asa_turn_id, asa_pieces_id,
                  asa_pieces_total, asa_pieces_max_remove, asa_pieces_amount)

if args['status']:
    with open("algonim.match", "rb") as f:
        match_data_bytes = f.read()
        f.close()
    match_data = msgpack.unpackb(match_data_bytes)
    player_stat = algod_client.account_info(args['<player_address>'])
    game_table_stat = algod_client.account_info(match_data['game_table'])
    asa_pieces_stat = algod_client.asset_info(match_data['asa_pieces_id'])

    print("\nMATCH TOTAL PIECES:\t\t" + str(asa_pieces_stat['total']))
    print("PIECES ON THE GAME TABLE:\t"
          + str(game_table_stat['assets'][str(match_data['asa_pieces_id'])][
              'amount']))

    if game_table_stat['assets'][str(match_data['asa_pieces_id'])][
              'amount'] != 0:
        if player_stat['assets'][str(match_data['asa_turn_id'])]['amount'] == 1:
            print("It's your turn! Play your best move!\n")
        else:
            print("Opponent is playing the turn...\n")
    else:
        print("The match is over!")
