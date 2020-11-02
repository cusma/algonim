"""AlgoNim, the first crypto-mini-game on Algorand! (by cusma)
Usage:
  algonim.py setup <dealer_mnemonic> <opponent_address> <hours_duration>
                   [--bet-amount=<ba>] [--pieces=<ps>] [--max-removal=<mr>]
  algonim.py join <opponent_mnemonic>
  algonim.py play <player_mnemonic> <asa_pieces_amount>
  algonim.py status <player_address>
  algonim.py close <player_address>
  algonim.py [--help]

Commands:
  setup    Dealer sets up a new AlgoNim match.
  join     Opponent joins the match.
  play     Play your turn.
  status   Display current match status.
  close    Close expired AlgoNim Bet Escrows.

Options:
  -b <ba> --bet-amount=<ba>     Set the bet amount in microAlgos
                                [default: 0].
  -p <ps> --pieces=<ps>         Set the total amount of pieces on game table
                                [default: 21].
  -m <mr> --max-removal=<mr>    Set maximum amount of pieces removal
                                [default: 4].
  -h --help
"""

import sys
from docopt import docopt
from algonim_moves import *


def main():
    if len(sys.argv) == 1:
        # Display help if no arguments, see:
        # https://github.com/docopt/docopt/issues/420#issuecomment-405018014
        sys.argv.append('--help')

    args = docopt(__doc__)

    algod_client = create_algod_client()
    try:
        algod_client.compile(
            compileTeal(Global.group_size() == Int(1), Mode.Signature))
    except Exception:
        raise ErrAlgodClientCompile

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
                    match_hours_timeout, microalgo_bet_amount,
                    asa_pieces_total, asa_pieces_max_remove)

    elif args['join']:
        with open("algonim.match", "rb") as f:
            match_data_bytes = f.read()
            f.close()
        match_data = msgpack.unpackb(match_data_bytes)

        opponent = {'pk': mnemonic.to_public_key(args['<opponent_mnemonic>']),
                    'sk': mnemonic.to_private_key(args['<opponent_mnemonic>'])}
        microalgo_bet_amount = match_data['microalgo_bet_amount']

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
        print("The Dealer wants to bet", microalgo_bet_amount * 10 ** -6,
              "ALGO.")
        join = input("Do you want to join the match? [y/N]")
        if join == 'y':
            # AlgoNim ASAs Opt-In
            asa_pieces_opt_in_txn = unsigned_asset_send(
                algod_client, opponent['pk'], opponent['pk'],
                match_data['asa_pieces_id'], 0)

            asa_pieces_opt_in_stxn = asa_pieces_opt_in_txn.sign(opponent['sk'])

            txid = algod_client.send_transactions([asa_pieces_opt_in_stxn])
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
            bet_sgtxn = [dealer_bet_stxn, opponent_bet_stxn]
            txid = algod_client.send_transactions(bet_sgtxn)
            print("\nPlayers betting...")
            print("Transaction ID: ", txid)
            wait_for_tx_confirmation(algod_client, txid)

            dealer_info = algod_client.account_info(match_data['dealer'])
            asa_pieces_total = next(
                (asa['params']['total'] for asa in
                 dealer_info['created-assets'] if
                 asa['index'] == match_data['asa_pieces_id']), None)

            print("                                ")
            print("              _       _         ")
            print("  /\/\   __ _| |_ ___| |__    _ ")
            print(" /    \ / _` | __/ __| '_ \  (_)")
            print("/ /\/\ \ (_| | || (__| | | |  _ ")
            print("\/    \/\__,_|\__\___|_| |_| (_)")
            print("                                ")
            print("MATCH DURATION:\t\t",
                  match_data['match_hours_timeout'] * 60, "min")
            print("PIECES ON GAME TABLE:\t", asa_pieces_total, "\n")
            print("RULES:")
            print("1. Players on each turn must remove at least 1 ASA Piece")
            print("2. Players on each turn must remove at most",
                  match_data['asa_pieces_max_remove'], "ASA Piece")
            print("3. Who removes the last ASA Piece form the Game Table wins "
                  + "the match!\n")
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

    elif args['play']:
        with open("algonim.match", "rb") as f:
            match_data_bytes = f.read()
            f.close()
        match_data = msgpack.unpackb(match_data_bytes)
        player = {'pk': mnemonic.to_public_key(args['<player_mnemonic>']),
                  'sk': mnemonic.to_private_key(args['<player_mnemonic>'])}
        asa_pieces_amount = int(args['<asa_pieces_amount>'])

        asa_pieces_id = match_data['asa_pieces_id']
        asa_pieces_max_remove = match_data['asa_pieces_max_remove']
        asa_turn_id = match_data['asa_turn_id']
        addr_sink = match_data['sink']
        sink_lsig = encoding.msgpack_decode(match_data['sink_lsig'])
        addr_game_table = match_data['game_table']
        game_table_lsig = encoding.msgpack_decode(
            match_data['game_table_lsig'])
        addr_dealer_bet_escrow = match_data['dealer_bet_escrow']
        dealer_bet_escrow_lsig = encoding.msgpack_decode(
            match_data['dealer_bet_escrow_lsig'])

        dealer_info = algod_client.account_info(match_data['dealer'])
        asa_pieces_total = next(
            (asa['params']['total'] for asa in dealer_info['created-assets'] if
             asa['index'] == match_data['asa_pieces_id']), None)

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
                      asa_pieces_max_remove, asa_pieces_amount,
                      asa_pieces_total)
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
                      asa_pieces_max_remove, asa_pieces_amount,
                      asa_pieces_total)

    elif args['status']:
        with open("algonim.match", "rb") as f:
            match_data_bytes = f.read()
            f.close()
        match_data = msgpack.unpackb(match_data_bytes)
        player_info = algod_client.account_info(args['<player_address>'])
        game_table_info = algod_client.account_info(match_data['game_table'])
        dealer_info = algod_client.account_info(match_data['dealer'])
        asa_pieces_total = next(
            (asa['params']['total'] for asa in dealer_info['created-assets'] if
             asa['index'] == match_data['asa_pieces_id']), None)
        pieces_on_table = next(
            (asa['amount'] for asa in game_table_info['assets'] if
             asa['asset-id'] == match_data['asa_pieces_id']), None)

        dealer_bet_escrow_info = algod_client.account_info(
            match_data['dealer_bet_escrow'])
        opponent_bet_escrow_info = algod_client.account_info(
            match_data['opponent_bet_escrow'])

        print("\nMATCH TOTAL PIECES:\t\t" + str(asa_pieces_total))
        print("PIECES ON THE GAME TABLE:\t" + str(pieces_on_table))

        if pieces_on_table != 0:
            if next((asa['amount'] for asa in player_info['assets'] if
                     asa['asset-id'] == match_data['asa_turn_id']), None) == 1:
                print("It's your turn! Play your best move!")
            else:
                print("Your opponent is playing the turn...")
        else:
            print("The match is over!")

        dealer_bet_escrow_amount = dealer_bet_escrow_info['amount']
        opponent_bet_escrow_amount = opponent_bet_escrow_info['amount']

        if args['<player_address>'] == match_data['dealer']:
            print("\nOPPONENT BET ESCROW AMOUNT:\t",
                  opponent_bet_escrow_amount)
            print("YOUR BET ESCROW AMOUNT:\t\t",
                  dealer_bet_escrow_amount)
            if dealer_bet_escrow_amount != 0:
                blockchain_params = algod_client.suggested_params()
                last_round = blockchain_params.first
                bet_escrow_expiry = match_data[
                                        'dealer_bet_escrow_expiry'] - last_round
                if bet_escrow_expiry > 0:
                    print("Your Bet Escrow is still locked.",
                          bet_escrow_expiry, "blocks left!\n")
                else:
                    print("Your Bet Escrow expired! " +
                          "You can claim your bet back.")
        elif args['<player_address>'] == match_data['opponent']:
            print("\nOPPONENT BET ESCROW AMOUNT:\t",
                  dealer_bet_escrow_amount)
            print("YOUR BET ESCROW AMOUNT:\t\t",
                  opponent_bet_escrow_amount)
            if opponent_bet_escrow_amount != 0:
                blockchain_params = algod_client.suggested_params()
                last_round = blockchain_params.first
                bet_escrow_expiry = match_data[
                                        'opponent_bet_escrow_expiry'] - last_round
                if bet_escrow_expiry > 0 and opponent_bet_escrow_amount != 0:
                    print("Your Bet Escrow is still locked.",
                          bet_escrow_expiry, "blocks left!\n")
                else:
                    print("Your Bet Escrow expired! " +
                          "You can claim your bet back.")
        else:
            print("Invalid player address for this match!")

    elif args['close']:
        with open("algonim.match", "rb") as f:
            match_data_bytes = f.read()
            f.close()
        match_data = msgpack.unpackb(match_data_bytes)
        if args['<player_address>'] == match_data['dealer']:
            dealer_bet_escrow_lsig = encoding.msgpack_decode(
                match_data['dealer_bet_escrow_lsig'])
            close_bet_escrow(algod_client,
                             match_data['dealer_bet_escrow'],
                             match_data['dealer'],
                             dealer_bet_escrow_lsig)
        elif args['<player_address>'] == match_data['opponent']:
            opponent_bet_escrow_lsig = encoding.msgpack_decode(
                match_data['opponent_bet_escrow_lsig'])
            close_bet_escrow(algod_client,
                             match_data['opponent_bet_escrow'],
                             match_data['opponent'],
                             opponent_bet_escrow_lsig)
        else:
            print("Invalid player address for this match!")

    else:
        print("\nError: read AlgoNim '--help'!\n")


class ErrAlgodClientCompile(Exception):
    def __init__(self):
        Exception.__init__(
            self, "\n\nAlgoNim failed to compile TEAL source code. Please:\n\n"
                  + "\t1. Go to your Algorand node data folder\n"
                  + "\t2. Copy 'config.json.example' as 'config.json'\n"
                  + "\t3. Open and edit 'config.json'\n"
                  + "\t4. Set \"EnableDeveloperAPI\" to true and save\n"
                  + "\t5. Restart your Algorand node: goal node restart\n")


if __name__ == "__main__":
    main()
