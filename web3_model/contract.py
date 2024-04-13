from eth_typing import ChecksumAddress
from web3 import Web3

from web3_model.wallet import Wallet


class Contract:
    """
    合约基类
    """
    # Web3 对象
    _w3: Web3 = None
    # 合约地址
    address: ChecksumAddress = None
    # 合约对象
    contract = None
    # ABI
    abi: str = None

    def __init__(self, w3: Web3, address: str, abi_path: str):
        """
        构造函数
        Args:
            w3:Web3对象
            address: 合约地址
            abi_path: ABI的路径
        """
        self._w3 = w3
        self.address = Web3.to_checksum_address(address)
        with open(abi_path, 'r') as f:
            self._abi = f.read()
        self.contract = w3.eth.contract(address=self.address, abi=self._abi)

    def encode_abi(self, fn_name: str, args: list):
        """
        编码ABI
        Args:
            fn_name:函数名称
            args:参数列表
        Returns:
            ABI
        """
        return self.contract.encodeABI(fn_name, args)

    def build_tx(self, from_address: ChecksumAddress, to_address: ChecksumAddress = None, value: int = 0, data=None, gas_price: int = None, gas: int = 0, nonce: int = 0):
        """
        构建交易
        Args:
            from_address: 发送地址
            to_address: 接收地址
            value: 金额
            data: ABI数据包
            gas: gas
            gas_price: gas_price
            nonce: nonce
        Returns:
            交易详情
        """
        tx = {
            "chainId": self._w3.eth.chain_id,
            "from": from_address,
            "gas": 0,
            "gasPrice": gas_price or self._w3.eth.gas_price,
            "nonce": nonce or self._w3.eth.get_transaction_count(from_address)
        }
        if to_address:
            tx["to"] = to_address
        if value:
            tx["value"] = value
        if data:
            tx["data"] = self._w3.to_bytes(hexstr=data)

        # 如果gas为0，自动估算gas
        tx['gas'] = self.gas_estimate(tx) if gas == 0 else gas

        return tx

    def send_tx(self, private_key: str, tx: dict):
        """
        打包并发送交易
        Args:
            private_key: 钱包私钥
            tx: 交易详情
        Returns:
            Hex格式的交易哈希
        """
        signed_tx = self._w3.eth.account.sign_transaction(tx, private_key)
        return Web3.to_hex(self._w3.eth.send_raw_transaction(signed_tx.rawTransaction))

    def build_and_send_tx(self, wallet: Wallet, to_address: ChecksumAddress, value: int = 0, data=None, gas_price: int = None, gas: int = 0, nonce: int = 0):
        """
        构建并发送交易
        Args:
            wallet: 钱包对象
            to_address: 接收地址
            value: 金额
            data: ABI数据包
            gas: gas
            gas_price: gas_price
            nonce: nonce
        Returns:
            Hex格式的交易哈希
        """
        tx = self.build_tx(wallet.address, to_address, value, data, gas_price, gas, nonce)
        return self.send_tx(wallet.private_key, tx)

    def call(self, function_name: str, *args):
        """
        调用合约函数
        Args:
            function_name:函数名称
            args:参数列表
        Returns:
            合约函数的返回值
        """
        return getattr(self.contract.functions, function_name)(*args).call()

    def call_by_tx(self, wallet: Wallet, function_name: str, *args):
        """
        通过交易调用合约函数
        Args:
            wallet:钱包对象
            function_name:函数名称
            args:参数列表
        Returns:
            交易哈希
        """
        txn = getattr(self.contract.functions, function_name)(*args).build_transaction(self.build_tx(wallet.address))
        return self.send_tx(wallet.private_key, txn)

    def call_with_value(self, wallet: Wallet, function_name: str, value: int, *args):
        """
        通过交易调用合约函数
        Args:
            wallet:钱包对象
            function_name:函数名称
            value: 金额
            args:参数列表
        Returns:
            交易哈希
        """
        txn = getattr(self.contract.functions, function_name)(*args).build_transaction(self.build_tx(wallet.address, value=value))
        return self.send_tx(wallet.private_key, txn)

    def gas_estimate(self, tx: dict):
        """
        估算交易的gas
        Args:
            tx: 交易详情
        Returns:
            gas
        """
        try:
            return self._w3.eth.estimate_gas(tx)
        except:
            # 如果预估失败，使用默认的Gas值
            return 2100000

    @staticmethod
    def to_unit256(amount, decimals=18):
        """
        将金额转换为unit256格式,并补齐精度
        Args:
            amount: 金额
            decimals: 精度,默认18
        Returns:
            unit256格式的金额
        """
        return Web3.to_wei(round(amount, decimals), 'ether')
