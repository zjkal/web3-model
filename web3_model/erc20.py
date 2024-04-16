from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from web3 import Web3

from web3_model.contract import Contract


class ERC20(Contract):
    """
    ERC20合约类
    """

    def __init__(self, w3: Web3, address: str, abi_path: str):
        """
        构造函数
        Args:
            w3:Web3对象
            address: 合约地址
            abi_path: ABI的路径
        """
        super().__init__(w3, address, abi_path)

    def approve(self, wallet: LocalAccount, contract: ChecksumAddress, amount: int = 2 ** 256 - 1):
        """
        发起授权
        Args:
            wallet: 本地账户对象
            contract: 授权的合约
            amount: 授权金额(默认为最大金额)
        Returns:
            授权结果的Hash
        """
        return self.call_by_tx(wallet, "approve", [contract, amount])

    def allowance(self, wallet: ChecksumAddress, contract: ChecksumAddress) -> int:
        """
        检查钱包地址对contact的授权金额
        Args:
            wallet: 钱包地址
            contract: 授权的合约
        Returns:
            授权金额
        """
        return self.call("allowance", [wallet, contract])

    def balance_of(self, wallet: ChecksumAddress) -> int:
        """
        查询钱包地址的余额
        Args:
            wallet: 钱包地址
        Returns:
            余额
        """
        return self.call("balanceOf", [wallet])

    def transfer(self, wallet: LocalAccount, to: ChecksumAddress, amount: int, gas: int = 0):
        """
        发起转账
        Args:
            wallet: 本地账户对象
            to: 接收地址
            amount: 转账金额
            gas: gas
        Returns:
            转账结果的Hash
        """
        return self.call_by_tx(wallet, "transfer", [to, amount], gas=gas)
