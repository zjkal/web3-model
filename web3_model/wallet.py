from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from web3 import Web3


class Wallet:
    """
    钱包类
    """
    # 钱包地址
    address: ChecksumAddress = None
    # 私钥
    private_key: str = None

    def __init__(self, address: str, private_key: str):
        """
        构造函数
        Args:
            address: 钱包地址
            private_key: 私钥
        """
        self.address = Web3.to_checksum_address(address)
        self.private_key = private_key

    @staticmethod
    def create_wallet(w3: Web3):
        """
        创建钱包
        Returns:
            Wallet: 钱包对象
        """
        new_wallet: LocalAccount = w3.eth.account.create()
        return Wallet(new_wallet.address, new_wallet.key.hex())
