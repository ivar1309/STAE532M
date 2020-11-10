#!/usr/bin/python3
 
import sys
import subprocess
import sqlite3
import json
 
def getAndDecodeRawTx(txid):
    out = subprocess.run(["smileycoin-cli", "getrawtransaction", txid], capture_output=True, text=True)
    raw = out.stdout.strip()
    out = subprocess.run(["smileycoin-cli", "decoderawtransaction", raw], capture_output=True, text=True)
    decoded = out.stdout.strip()
    return raw, decoded
 
def getSenderAddress(tx):
    senderTxId = tx['vin'][0]['txid']
    senderVout = tx['vin'][0]['vout']
    raw, decoded = getAndDecodeRawTx(senderTxId)
    decodedJSON = json.loads(decoded)
    senderAddress = [v['scriptPubKey']['addresses'] for v in decodedJSON['vout'] if v['n'] == senderVout]
    return senderAddress[0][0]
 
def getSenderValue(tx, myAddress):
    senderValue = [v['value'] for v in tx['vout'] if (myAddress in v['scriptPubKey']['addresses'])]
    return senderValue[0]
 
myAddress = "ADDRESS_TO_MONITOR"
 
conn = sqlite3.connect("smly.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()
 
txid = sys.argv[1]
print("txid: {}".format(txid))
 
isTxidInDB = c.execute("SELECT COUNT(*) FROM Transactions WHERE txid=?", (txid,)).fetchall()
 
#  If this txid is in the db then quit.
if (isTxidInDB[0][0] > 0):
    exit()
 
raw, decoded = getAndDecodeRawTx(txid)
decodedJSON = json.loads(decoded)
 
senderAddress = getSenderAddress(decodedJSON)
senderValue = getSenderValue(decodedJSON, myAddress)
 
c.execute("INSERT INTO Transactions VALUES (?, ?, ?)", (txid, raw, decoded))
c.execute("INSERT INTO Senders VALUES (?, ?, ?)", (senderAddress, senderValue, ''))
conn.commit()
conn.close()