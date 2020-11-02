import msgpack
import base64
from algosdk import encoding, mnemonic, transaction
from algonim_asa import *
from algonim_asc1 import *


def bet_atomic_transfer(algod_client, dealer, addr_opponent,
                        addr_dealer_bet_escrow, addr_opponent_bet_escrow,
                        microalgo_bet_amount):
    """HELP bet_atomic_transfer:
        (AlgodClient, dict, str, str, str, int) - Returns Bet Atomic Transfer
        partially signed by the Dealer, to be signed by the Opponent.
    """

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


def play_last_turn(algod_client, player, addr_adversary,
                   addr_game_table, game_table_lsig,
                   addr_sink, sink_lsig,
                   addr_adversary_bet_escrow, adversary_bet_escrow_lsig,
                   asa_turn_id, asa_pieces_id,
                   asa_pieces_amount, asa_pieces_total):
    """HELP play_last_turn:
        (AlgodClient, dict, str, str, str, str, str,  str, str, int, int, int,
        int) - Play last turn moving ASA Pieces form the Game Table to the
        Sink and show the winning proof to the opponent's Bet Escrow.
    """

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

    sgtxn = [stxn0, lstxn1, lstxn2, lstxn3]
    txid = algod_client.send_transactions(sgtxn)
    print("\nI WON !!! Arrivederci " + addr_adversary)
    print("Transaction ID: ", txid)
    wait_for_tx_confirmation(algod_client, txid)


def play_turn(algod_client, player, addr_adversary,
              addr_game_table, game_table_lsig,
              addr_sink, sink_lsig,
              addr_adversary_bet_escrow, adversary_bet_escrow_lsig,
              asa_turn_id, asa_pieces_id,
              asa_pieces_max_remove, asa_pieces_amount, asa_pieces_total):
    """HELP play_turn:
        (AlgodClient, dict, str, str, str, str, str,  str, str, int, int, int,
        int) - Play turn moving ASA Pieces form the Game Table to the Sink.
    """

    game_table_info = algod_client.account_info(addr_game_table)
    pieces_on_table = next(
        (asa['amount'] for asa in game_table_info['assets'] if
         asa['asset-id'] == asa_pieces_id), None)

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
        sgtxn = [stxn0, lstxn1]
        txid = algod_client.send_transactions(sgtxn)
        print("\nRemoving", asa_pieces_amount, "pieces from the Game Table...")
        print("Transaction ID: ", txid)
        wait_for_tx_confirmation(algod_client, txid)
    else:
        play_last_turn(algod_client, player, addr_adversary,
                       addr_game_table, game_table_lsig,
                       addr_sink, sink_lsig,
                       addr_adversary_bet_escrow, adversary_bet_escrow_lsig,
                       asa_turn_id, asa_pieces_id,
                       asa_pieces_amount, asa_pieces_total)


def match_setup(algod_client, dealer_passphrase, addr_opponent,
                match_hours_timeout, microalgo_bet_amount, asa_pieces_total,
                asa_pieces_max_remove):
    """HELP match_setup:
        (AlgodClient, str, str, float, int, int, int) - Sets up a new AlgoNim
        match.
    """

    # AlgoNim Players
    # Palyer 1 (Dealer) - Match Set Up costs about: 0.8 ALGO
    dealer = {'pk': mnemonic.to_public_key(dealer_passphrase),
              'sk': mnemonic.to_private_key(dealer_passphrase)}

    # Player 2 (Opponent) - Must Opt-In AlgoNim ASAs to play the match
    opponent = {'pk': addr_opponent}

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
        asa_pieces_total, asa_pieces_id, dealer['pk'], opponent['pk'])
    asc1_sink_compiled = algod_client.compile(asc1_sink_source)

    sink_lsig = transaction.LogicSig(
        base64.decodebytes(asc1_sink_compiled['result'].encode()))
    addr_sink = asc1_sink_compiled['hash']

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
        asa_pieces_total, asa_pieces_id, asa_pieces_max_remove, asa_turn_id,
        dealer['pk'], opponent['pk'], addr_sink)
    asc1_game_table_compiled = algod_client.compile(asc1_game_table_source)

    game_table_lsig = transaction.LogicSig(
        base64.decodebytes(asc1_game_table_compiled['result'].encode()))
    addr_game_table = asc1_game_table_compiled['hash']

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
    dealer_sgtxn = [gt_opt_in_lstxn, deal_pieces_stxn]
    txid = algod_client.send_transactions(dealer_sgtxn)
    print("Transaction ID: ", txid)
    wait_for_tx_confirmation(algod_client, txid)

    # TEAL: AlgoNim ASC1 Bet Escrow
    print("")
    print("Dealer writing AlgoNim ASC1 Bet Escrow TEAL for Palyer 1...")
    asc1_dealer_bet_escrow_source, dealer_bet_escrow_expiry_block = asc1_bet_escrow_teal(
        algod_client, asa_pieces_total, asa_pieces_id, asa_turn_id,
        dealer['pk'], opponent['pk'], addr_sink, addr_game_table,
        match_hours_timeout)
    asc1_dealer_bet_escrow_compiled = algod_client.compile(
        asc1_dealer_bet_escrow_source)

    dealer_bet_escrow_lsig = transaction.LogicSig(
        base64.decodebytes(asc1_dealer_bet_escrow_compiled['result'].encode()))
    addr_dealer_bet_escrow = asc1_dealer_bet_escrow_compiled['hash']

    print("")
    print("Dealer writing AlgoNim ASC1 Bet Escrow TEAL for Palyer 2...")
    asc1_opponent_bet_escrow_source, opponent_bet_escrow_expiry_block = asc1_bet_escrow_teal(
        algod_client, asa_pieces_total, asa_pieces_id, asa_turn_id,
        opponent['pk'], dealer['pk'], addr_sink, addr_game_table,
        match_hours_timeout)
    asc1_opponent_bet_escrow_compiled = algod_client.compile(
        asc1_opponent_bet_escrow_source)

    opponent_bet_escrow_lsig = transaction.LogicSig(
        base64.decodebytes(asc1_opponent_bet_escrow_compiled['result'].encode()))
    addr_opponent_bet_escrow = asc1_opponent_bet_escrow_compiled['hash']

    # Initialize AlgoNim ASC1 Escrows with 0.1 ALGO
    print("")
    print("Initializing Bet Escrow Accounts...")
    send(algod_client, dealer, addr_dealer_bet_escrow, 100000)
    print("")
    send(algod_client, dealer, addr_opponent_bet_escrow, 100000)

    # Creating Bet Atomic Transfer to be signed by the Opponent
    dealer_bet_stxn, opponent_bet_txn = bet_atomic_transfer(
        algod_client, dealer, opponent['pk'], addr_dealer_bet_escrow,
        addr_opponent_bet_escrow, microalgo_bet_amount)

    match_data = {}
    match_data['dealer'] = dealer['pk']
    match_data['opponent'] = opponent['pk']
    match_data['asa_pieces_id'] = asa_pieces_id
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
    match_data['dealer_bet_escrow_expiry'] = dealer_bet_escrow_expiry_block
    match_data['opponent_bet_escrow_expiry'] = opponent_bet_escrow_expiry_block
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
    print("PIECES ON GAME TABLE:\t", asa_pieces_total, "\n")
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
    print("\nSend 'algonim.match' file to your opponent join the match!\n")
    print("May the best win!\n")


def close_bet_escrow(algod_client, addr_bet_escrow, addr_owner,
                     bet_escrow_lsig):
    """HELP close_escrow:
        (AlgodClient, str, str, LogicSig) - Closes the expired Bet Escrow.
    """

    txn0 = unsigned_closeto(algod_client, addr_bet_escrow, addr_owner)
    lstxn0 = transaction.LogicSigTransaction(txn0, bet_escrow_lsig)
    txid = algod_client.send_transactions([lstxn0])
    print("\nClosing expired Bet Escrow: " + addr_bet_escrow)
    print("Transaction ID: ", txid)
    wait_for_tx_confirmation(algod_client, txid)
