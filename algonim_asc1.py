from pyteal import *


def asc1_sink_teal(asa_pieces_total,
                   asa_pieces_id,
                   player_alice,
                   player_bob):
    """HELP asc1_sink_teal:
        (int, int, str, str) - Returns AlgoNim ASC1 Sink raw TEAL.
    """
    # AlgoNim ASC1 Sink controls the following conditions:
    # 1. AlgoNim ASA Pieces Opt-In
    # 2. Empty Sink: Alice or Bob remove all the AlgoNim ASA Pieces total
    # supply from the Sink as winning proof.

    # ASC1 Constants:
    tmpl_fee = Int(1000)

    # ASC1 Logic:
    # 1. AlgoNim ASA Pieces Opt-In
    asa_pieces_opt_in = And(Global.group_size() == Int(1),
                            Txn.group_index() == Int(0),
                            Txn.type_enum() == Int(4),
                            Txn.fee() <= tmpl_fee,
                            Txn.xfer_asset() == Int(asa_pieces_id),
                            Txn.asset_amount() == Int(0),
                            Txn.asset_close_to() == Global.zero_address(),
                            Txn.rekey_to() == Global.zero_address())

    # 2. Empty Sink
    empty_sink_alice = And(Global.group_size() == Int(4),
                           Txn.group_index() == Int(2),
                           Txn.type_enum() == Int(4),
                           Txn.fee() <= tmpl_fee,
                           Txn.xfer_asset() == Int(asa_pieces_id),
                           Txn.asset_amount() == Int(asa_pieces_total),
                           Txn.asset_receiver() == Addr(player_alice),
                           Txn.asset_close_to() == Global.zero_address(),
                           Txn.rekey_to() == Global.zero_address())

    empty_sink_bob = And(Global.group_size() == Int(4),
                         Txn.group_index() == Int(2),
                         Txn.type_enum() == Int(4),
                         Txn.fee() <= tmpl_fee,
                         Txn.xfer_asset() == Int(asa_pieces_id),
                         Txn.asset_amount() == Int(asa_pieces_total),
                         Txn.asset_receiver() == Addr(player_bob),
                         Txn.asset_close_to() == Global.zero_address(),
                         Txn.rekey_to() == Global.zero_address())

    empty_sink = Or(empty_sink_alice, empty_sink_bob)
    asc1_sink = Or(asa_pieces_opt_in, empty_sink)
    return compileTeal(asc1_sink, Mode.Signature)


def asc1_game_table_teal(asa_pieces_total,
                         asa_pieces_id,
                         asa_pieces_max_remove,
                         asa_turn_id,
                         player_alice,
                         player_bob,
                         asc1_sink):
    """HELP asc1_game_table_teal:
        (int, int, int, int, int, str, str, str) - Returns AlgoNim ASC1
        Game Table raw TEAL
    """
    # AlgoNim ASC1 Game Table controls the following conditions:
    # 1. Dealer - Funding Game Table with AlgoNim ASA Pieces
    # 2. Play Turn - Player correctly removes ASA Pieces from the Game Table

    # ASC1 Constants:
    tmpl_fee = Int(1000)

    # ASC1 Logic:
    # 1. Dealer
    asa_pieces_opt_in = And(Global.group_size() == Int(2),
                            Txn.group_index() == Int(0),
                            Gtxn[0].type_enum() == Int(4),
                            Gtxn[0].fee() <= tmpl_fee,
                            Gtxn[0].xfer_asset() == Int(asa_pieces_id),
                            Gtxn[0].asset_amount() == Int(0),
                            Gtxn[0].asset_close_to() == Global.zero_address(),
                            Gtxn[0].rekey_to() == Global.zero_address())

    game_table_setup = And(Global.group_size() == Int(2),
                           Gtxn[1].type_enum() == Int(4),
                           Gtxn[1].fee() <= tmpl_fee,
                           Gtxn[1].xfer_asset() == Int(asa_pieces_id),
                           Gtxn[1].asset_amount() == Int(asa_pieces_total),
                           Gtxn[1].sender() == Addr(player_alice),
                           Gtxn[1].asset_close_to() == Global.zero_address(),
                           Gtxn[1].rekey_to() == Global.zero_address())

    dealer = And(asa_pieces_opt_in, game_table_setup)

    # 2. Play Turn
    play_turn_type = Or(Global.group_size() == Int(2),
                        Global.group_size() == Int(4))

    change_turn_alice_to_bob = And(play_turn_type,
                                   Gtxn[0].type_enum() == Int(4),
                                   Gtxn[0].fee() <= tmpl_fee,
                                   Gtxn[0].xfer_asset() == Int(asa_turn_id),
                                   Gtxn[0].asset_amount() == Int(1),
                                   Gtxn[0].sender() == Addr(player_alice),
                                   Gtxn[0].asset_receiver() == Addr(player_bob),
                                   Gtxn[0].asset_close_to() == Global.zero_address(),
                                   Gtxn[0].rekey_to() == Global.zero_address())

    change_turn_bob_to_alice = And(play_turn_type,
                                   Gtxn[0].type_enum() == Int(4),
                                   Gtxn[0].fee() <= tmpl_fee,
                                   Gtxn[0].xfer_asset() == Int(asa_turn_id),
                                   Gtxn[0].asset_amount() == Int(1),
                                   Gtxn[0].sender() == Addr(player_bob),
                                   Gtxn[0].asset_receiver() == Addr(player_alice),
                                   Gtxn[0].asset_close_to() == Global.zero_address(),
                                   Gtxn[0].rekey_to() == Global.zero_address())

    change_turn = Or(change_turn_alice_to_bob, change_turn_bob_to_alice)

    remove_asa_pieces = And(play_turn_type,
                            Txn.group_index() == Int(1),
                            Gtxn[1].type_enum() == Int(4),
                            Gtxn[1].fee() <= tmpl_fee,
                            Gtxn[1].xfer_asset() == Int(asa_pieces_id),
                            Gtxn[1].asset_amount() >= Int(1),
                            Gtxn[1].asset_amount() <= Int(asa_pieces_max_remove),
                            Gtxn[1].asset_receiver() == Addr(asc1_sink),
                            Gtxn[1].asset_close_to() == Global.zero_address(),
                            Gtxn[1].rekey_to() == Global.zero_address())

    play_turn = And(change_turn, remove_asa_pieces)
    asc1_game_table = Or(dealer, play_turn)
    return compileTeal(asc1_game_table, Mode.Signature)


def asc1_bet_escrow_teal(algod_client,
                         asa_pieces_total,
                         asa_pieces_id,
                         asa_turn_id,
                         addr_escrow_owner,
                         addr_adversary_player,
                         asc1_sink,
                         asc1_game_table,
                         match_hours_timeout):
    """HELP asc1_sink_raw_teal:
        (AlgodClient, int, int, int, str, str, str, str, float) - Returns
        AlgoNim ASC1 Bet Escrow raw TEAL
    """
    # AlgoNim Bet Escrow controls the following conditions:
    # 1. Opponent wins
    # 2. Bet escrow expires

    # Blockchain Parameters
    blockchain_params = algod_client.suggested_params()
    first_valid = blockchain_params.first

    # AlgoNim Bet Escrow expiration
    match_blocks_duration = int(match_hours_timeout * 3600 // 5)
    bet_escrow_expiry_block = first_valid + match_blocks_duration
    print("AlgoNim Bet Escrows Expiry block:", bet_escrow_expiry_block)

    # ASC1 Constants:
    tmpl_fee = Int(1000)

    # ASC1 Logic:
    # 1. Opponent wins
    change_turn = And(Global.group_size() == Int(4),
                      Gtxn[0].type_enum() == Int(4),
                      Gtxn[0].fee() <= tmpl_fee,
                      Gtxn[0].xfer_asset() == Int(asa_turn_id),
                      Gtxn[0].asset_amount() == Int(1),
                      Gtxn[0].sender() == Addr(addr_adversary_player),
                      Gtxn[0].asset_receiver() == Addr(addr_escrow_owner),
                      Gtxn[0].asset_close_to() == Global.zero_address(),
                      Gtxn[0].rekey_to() == Global.zero_address())

    last_move = And(Global.group_size() == Int(4),
                    Gtxn[1].type_enum() == Int(4),
                    Gtxn[1].fee() <= tmpl_fee,
                    Gtxn[1].xfer_asset() == Int(asa_pieces_id),
                    Gtxn[1].sender() == Addr(asc1_game_table),
                    Gtxn[1].asset_receiver() == Addr(asc1_sink),
                    Gtxn[1].asset_close_to() == Global.zero_address(),
                    Gtxn[1].rekey_to() == Global.zero_address())

    winner_proof = And(Global.group_size() == Int(4),
                       Gtxn[2].type_enum() == Int(4),
                       Gtxn[2].fee() <= tmpl_fee,
                       Gtxn[2].xfer_asset() == Int(asa_pieces_id),
                       Gtxn[2].sender() == Addr(asc1_sink),
                       Gtxn[2].asset_receiver() == Addr(addr_adversary_player),
                       Gtxn[2].asset_amount() == Int(asa_pieces_total),
                       Gtxn[2].asset_close_to() == Global.zero_address(),
                       Gtxn[2].rekey_to() == Global.zero_address())

    collect_reward = And(Global.group_size() == Int(4),
                         Txn.group_index() == Int(3),
                         Gtxn[3].type_enum() == Int(1),
                         Gtxn[3].fee() <= tmpl_fee,
                         Gtxn[3].receiver() == Addr(addr_adversary_player),
                         Gtxn[3].amount() == Int(0),
                         Gtxn[3].close_remainder_to() == Addr(addr_adversary_player),
                         Gtxn[3].rekey_to() == Global.zero_address())

    win = And(change_turn, last_move, winner_proof, collect_reward)

    # 2. Bet Escrow Timeout
    timeout = And(Global.group_size() == Int(1),
                  Txn.group_index() == Int(0),
                  Txn.type_enum() == Int(1),
                  Txn.fee() <= tmpl_fee,
                  Txn.receiver() == Addr(addr_escrow_owner),
                  Txn.amount() == Int(0),
                  Txn.close_remainder_to() == Addr(addr_escrow_owner),
                  Txn.first_valid() > Int(bet_escrow_expiry_block),
                  Txn.rekey_to() == Global.zero_address())

    # 3. Close Bet Escrow
    asc1_bet_escrow = And(
        Cond([Global.group_size() == Int(4), win],
             [Global.group_size() == Int(1), timeout]),
        Int(1) == Int(1))
    return compileTeal(asc1_bet_escrow, Mode.Signature), bet_escrow_expiry_block
