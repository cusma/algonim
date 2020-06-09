import os

from algosdk import algod, transaction


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
