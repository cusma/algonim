from algosdk import transaction
from algonim_lib import *


def asa_pieces_create(algod_client,
                      asset_creator,
                      total):
    """HELP asa_pieces_create:
        (AlgodClient, dict, int) - Returns AlgoNim ASA Pieces Asset ID.
    """
    assert type(total) == int
    # Get network suggested params for transactions.
    params = algod_client.suggested_params()
    first_valid = params.first
    last_valid = first_valid + 1000
    gh = params.gh
    min_fee = params.min_fee
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
        ptx = algod_client.pending_transaction_info(txid)
        asa_id = ptx['asset-index']
        print("AlgoNim ASA Piece ID: {}".format(asa_id))
        return asa_id
    except Exception as e:
        print(e)


def asa_turn_create(algod_client,
                    asset_creator):
    """HELP asa_turn_create:
        (AlgodClient, dict) - Returns AlgoNim ASA Turn Asset ID.
    """
    # Get network suggested params for transactions.
    params = algod_client.suggested_params()
    first_valid = params.first
    last_valid = first_valid + 1000
    gh = params.gh
    min_fee = params.min_fee
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
        ptx = algod_client.pending_transaction_info(txid)
        asa_id = ptx['asset-index']
        print("AlgoNim ASA Turn ID: {}".format(asa_id))
        return asa_id
    except Exception as e:
        print(e)


def asa_score_create(algod_client,
                     asset_creator):
    """HELP asa_score_create:
        (AlgodClient, dict) - Returns AlgoNim ASA Score Asset ID.
    """
    # Get network suggested params for transactions.
    params = algod_client.suggested_params()
    first_valid = params.first
    last_valid = first_valid + 1000
    gh = params.gh
    min_fee = params.min_fee
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
        ptx = algod_client.pending_transaction_info(txid)
        asa_id = ptx['asset-index']
        print("AlgoNim ASA Score ID: {}".format(asa_id))
        return asa_id
    except Exception as e:
        print(e)
