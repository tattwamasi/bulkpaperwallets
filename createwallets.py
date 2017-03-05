#
# Bulk Paper Wallet
# (c) March 2017 1200 Development Amsterdam
#
# Generate Bitcoin Paper Wallets in Bulk and fund them. Wallets will be saved as PDF files.
#

import sys
import os
import argparse
from builtins import input
import binascii
import qrcode
import pdfkit
from jinja2 import Template
from bitcoinlib.wallets import HDWallet, wallet_exists
from bitcoinlib.keys import Key, HDKey
from bitcoinlib.transactions import Transaction, Input, Output
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.services.services import Service


# Bitcoins uitdelen definitions
DEFAULT_NETWORK = 'bitcoin'
DEFAULT_WALLET_NAME = "Bulk Paper Wallet"
# OUTPUT_NUMBER = 5
# OUTPUT_FEE = 10000
# OUTPUT_AMOUNT = int((135914715 / 5) - OUTPUT_FEE)
# PK_SENTENCE = 'dizzy shoe popular funny purse street drink jazz call key local movie'

INSTALL_DIR = os.path.dirname(__file__)
WALLET_DIR = os.path.join(INSTALL_DIR, 'wallets')
if not os.path.exists(WALLET_DIR):
    os.makedirs(WALLET_DIR)

# Unspent transaction output to use as input
# TODO: Allow more then 1 input
# input_utxo = 'adee8bdd011f60e52949b65b069ff9f19fc220815fdc1a6034613ed1f6b775f1'
# input_index = 0
# input_pk = 'cRMjy1LLMPsVU4uaAt3br8Ft5vdJLx6prY4Sx7WjPARrpYAnVEkV'


class BulkPaperWallet(HDWallet):

    def create_bulk_transaction(self, wallet):
        # Create Transaction and add input and outputs
        t = Transaction(network=self.network)
        ki = Key(input_pk)
        t.add_input(input_utxo, input_index, public_key=ki.public())

        output_keys = []
        for _ in range(0, OUTPUT_NUMBER):
            nk = wallet.new_key()
            t.add_output(OUTPUT_AMOUNT, address=nk.address)
            output_keys.append(nk)

        t.sign(ki.private_byte(), 0)
        if not t.verify():
            raise Exception("Could not verify this transaction: %s" % t.get())

        return

    def create_paper_wallets(self, output_keys):
        # Create Paper wallets
        for wallet_key in output_keys:
            address_img = qrcode.make(wallet_key.address)
            filename_pre = "%s/%d-" % (WALLET_DIR, wallet_key.key_id)
            address_img.save(filename_pre+'address.png', 'PNG')

            priv_img = qrcode.make(wallet_key.k.private().wif())
            priv_img.save(filename_pre+'privatekey.png', 'PNG')

            f = open('wallet_template.html', 'r')
            template = Template(f.read())
            wallet_name = "%s %d" % (self.wallet_name, wallet_key.key_id)
            wallet_str = template.render(
                install_dir=INSTALL_DIR,
                filename_pre=filename_pre,
                wallet_name=wallet_name,
                private_key=wallet_key.k.private().wif(),
                address=wallet_key.address)
            pdfkit.from_string(wallet_str, filename_pre+'wallet.pdf')


def parse_args():
    parser = argparse.ArgumentParser(description='Create Bulk Paper Wallets')
    parser.add_argument('--wallet_name', '-w', default=DEFAULT_WALLET_NAME,
                        help="Name of wallet to create or open. Used to store your all your wallet keys "
                             "and will be printed on each paper wallet")
    parser.add_argument('--network', '-n', help="Specify 'bitcoin', 'testnet' or other supported network",
                        default=DEFAULT_NETWORK)
    group1 = parser.add_mutually_exclusive_group(required=True)
    group1.add_argument('--outputs', '-o', nargs="*", type=float,
                        help="List of output values. For example '-o 1 2 3' creates 3 wallets with a value of "
                             "1, 2 and 3 bitcoin successively")
    group1.add_argument('--outputs-import', '-f',
                        help="Filename of comma seperated value list of output values and optional wallet names. "
                             "Example: 1.51, John")
    parser.add_argument('--outputs-repeat', '-r', type=int,
                        help="Repeat the outputs OUTPUTS_REPEAT times. For example 'createwallet.py -o 5 -r 10' "
                             "will create 10 wallets with 5 bitcoin")
    parser.add_argument('--input-key', '-i',
                        help="Private key of wallet to create transaction input. If not specified a private key "
                             "and address to send bitcoins to will be created. The program must wait before the"
                             "transfer arives before it can continue")
    parser.add_argument('--wallet_remove',
                        help="Name of wallet to remove, all keys and related information will be deleted")
    parser.add_argument('--recover-wallet-passphrase',
                        help="Passphrase of 12 words to recover and regenerate a previous wallet")

    pa = parser.parse_args()
    if pa.outputs_repeat and pa.outputs is None:
        parser = argparse.ArgumentParser()
        parser.error("--output_repeat requires --outputs")
    return pa

if __name__ == '__main__':
    args = parse_args()

    wallet_name = args.wallet_name
    network = args.network

    print("Create or open wallet '%s' (%s network)" % (wallet_name, network))

    print("Output amounts %s" % args.outputs)

    sys.exit()
    if wallet_exists(wallet_name):
        wallet = BulkPaperWallet(wallet_name)
    else:
        if not PK_SENTENCE:
            words = Mnemonic('english').generate()
            print("Your mnemonic private key sentence is: %s" % words)
            print("\nPlease write down on paper and backup. IF YOU LOSE THIS PRIVATE KEY ALL COINS ARE LOST!")
            inp = input("Type 'yes' if you understood and wrote down your key: ")
            if inp not in ['yes', 'Yes', 'YES']:
                print("Exiting...")
                sys.exit()
        else:
            words = PK_SENTENCE

        seed = binascii.hexlify(Mnemonic().to_seed(words))
        hdkey = HDKey().from_seed(seed, network=network)
        wallet = BulkPaperWallet.create(name=wallet_name, network=network, key=hdkey.extended_wif())

    wallet.info(detail=3)
