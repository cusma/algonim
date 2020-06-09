import json

from algosdk import transaction

from algonim_lib import *


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