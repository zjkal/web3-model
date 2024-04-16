from typing import List, Any

from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from web3 import Web3


def to_unit(amount_float, decimals=18):
    """
    将float金额转换为unit格式
    Args:
        amount_float: 金额
        decimals: 精度,默认18
    Returns:
        unit格式的金额
    """
    return round(amount_float, decimals) * 10 ** decimals


def from_unit(amount_uint, decimals=18):
    """
    将unit格式的金额转换为float金额
    Args:
        amount_uint: unit格式的金额
        decimals: 精度,默认18
    Returns:
        普通金额
    """
    return amount_uint / 10 ** decimals


class Contract:
    """
    合约基类
    """
    # Web3 对象
    w3: Web3 = None
    # 合约地址
    address: ChecksumAddress = None
    # 合约对象
    contract = None
    # ABI
    abi: str = None

    def __init__(self,
                 w3: Web3,
                 address: str,
                 abi_path: str
                 ):
        """
        构造函数
        Args:
            w3:Web3对象
            address: 合约地址
            abi_path: ABI的路径
        """
        self.w3 = w3
        self.address = Web3.to_checksum_address(address)
        with open(abi_path, 'r') as f:
            self._abi = f.read()
        self.contract = w3.eth.contract(address=self.address, abi=self._abi)

    def encode_abi(self,
                   function_name: str,
                   function_args: List
                   ):
        """
        编码ABI
        Args:
            function_name:函数名称
            function_args:参数列表
        Returns:
            ABI
        """
        return self.contract.encodeABI(function_name, function_args)

    def build_tx(self,
                 from_address: ChecksumAddress,
                 to_address: ChecksumAddress = None,
                 value: int = 0,
                 data: Any = None,
                 gas_price: int = None,
                 gas: int = 0,
                 nonce: int = 0
                 ):
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
            "chainId": self.w3.eth.chain_id,
            "from": from_address,
            "gasPrice": gas_price or self.w3.eth.gas_price,
            "gas": gas or 210000,
            "nonce": nonce or self.w3.eth.get_transaction_count(from_address)
        }
        if to_address:
            tx["to"] = to_address
        if value:
            tx["value"] = value
        if data:
            tx["data"] = self.w3.to_bytes(hexstr=data)

        return tx

    def send_tx(self,
                private_key: str,
                tx: dict
                ):
        """
        打包并发送交易
        Args:
            private_key: 钱包私钥
            tx: 交易详情
        Returns:
            Hex格式的交易哈希
        """
        return Web3.to_hex(self.w3.eth.send_raw_transaction(self.w3.eth.account.sign_transaction(tx, private_key).rawTransaction))

    def build_and_send_tx(self,
                          wallet: LocalAccount,
                          to_address: ChecksumAddress,
                          value: int = 0,
                          data: Any = None,
                          gas_price: int = None,
                          gas: int = 0,
                          nonce: int = 0):
        """
        构建并发送交易
        Args:
            wallet: 本地账户对象
            to_address: 接收地址
            value: 金额
            data: ABI数据包
            gas: gas
            gas_price: gas_price
            nonce: nonce
        Returns:
            Hex格式的交易哈希
        """
        return self.send_tx(wallet.key, self.build_tx(wallet.address, to_address, value, data, gas_price, gas, nonce))

    def build_call(self,
                   function_name: str,
                   function_args: List
                   ):
        """
        构建合约函数调用
        Args:
            function_name:函数名称
            function_args:参数列表
        Returns:
            合约函数的返回值
        """
        return getattr(self.contract.functions, function_name)(*function_args)

    def call(self,
             function_name: str,
             function_args: List
             ):
        """
        调用合约函数
        Args:
            function_name:函数名称
            function_args:参数列表
        Returns:
            合约函数的返回值
        """
        return self.build_call(function_name, function_args).call()

    def call_by_tx(self,
                   wallet: LocalAccount,
                   function_name: str,
                   function_args: List,
                   value: int = 0,
                   gas: int = 0
                   ):
        """
        通过交易调用合约函数
        Args:
            wallet:本地账户对象
            function_name:函数名称
            function_args:参数列表
            value: 金额
            gas: gas
        Returns:
            交易哈希
        """
        return self.send_tx(wallet.key, self.build_call(function_name, function_args).build_transaction(self.build_tx(wallet.address, value=value, gas=gas)))

    def estimate_tx_gas(self, tx: dict):
        """
        估算发起交易的gas
        Args:
            tx: 交易详情字典
        Returns:
            gas
        """
        return self.w3.eth.estimate_gas(tx)

    def estimate_call_gas(self, call: Any, tx: dict):
        """
        估算合约函数调用的gas
        Args:
            call: 合约函数调用对象
            tx: 交易详情字典
        Returns:
            gas
        """
        return call.estimate_gas({tx})


class Caller:
    """
    调用者类
    """
    # 合约对象
    _contract: Contract = None
    # 本地账户对象
    _wallet: LocalAccount = None

    # 合约函数对象
    _fn = None

    # 交易详情
    _tx: dict = None

    def __init__(self,
                 contract: Contract,
                 wallet: LocalAccount = None
                 ):
        """
        构造函数
        Args:
            contract: 合约对象
            wallet: 本地账户对象
        """
        self._contract = contract
        self._wallet = wallet

    def build(self,
              function_name: str,
              function_args: List,
              ) -> 'Caller':
        """
        构建合约函数对象
        Args:
            function_name:函数名称
            function_args:函数参数列表
        Returns:
            调用者类
        """
        self._fn = self._contract.build_call(function_name, function_args)
        return self

    def build_by_tx(self,
                    function_name: str,
                    function_args: List,
                    value: int = 0,
                    gas: int = 0,
                    gas_price: int = 0,
                    nonce: int = 0
                    ) -> 'Caller':
        """
        构建合约函数对象
        Args:
            function_name:函数名称
            function_args:函数参数列表
            value: 金额
            gas: gas
            gas_price: gas_price
            nonce: nonce
        Returns:
            调用者类
        """
        self._fn = self._contract.build_call(function_name, function_args)
        self._tx = self._contract.build_tx(self._wallet.address, value=value, gas=gas, gas_price=gas_price, nonce=nonce)
        return self

    def estimate_gas_fee(self) -> int:
        """
        估算gas费用(单位Wei)
        Returns:
            gas
        """
        # 如果没有设置gas,则自动预估
        self._tx['gas'] = self._tx['gas'] or self._contract.estimate_tx_gas(self._tx)
        # 如果没有设置gas_price,则从链上中获取
        self._tx['gasPrice'] = self._tx['gasPrice'] or self._contract.w3.eth.gas_price

        return self._tx['gas']

    def send(self):
        """
        发送交易
        Returns:
            交易哈希
        """
        if self._tx:
            # 如果gas为0,则计算gas
            if not self._tx["gas"]:
                self.estimate_gas_fee()
            # 构建并发送交易
            return self._contract.send_tx(self._wallet.key, self._fn.build_transaction(self._tx))
        else:
            # 直接发起函数调用
            return self._fn.call()


class Sender:
    """
    交易发送者类
    """
    # 合约对象
    _contract: Contract = None
    # 本地账户对象
    _wallet: LocalAccount = None

    # 交易详情
    _tx: dict = None

    def __init__(self,
                 contract: Contract,
                 wallet: LocalAccount = None
                 ):
        """
        构造函数
        Args:
            contract: 合约对象
            wallet: 本地账户对象
        """
        self._contract = contract
        self._wallet = wallet

    def build(self,
              to_address: ChecksumAddress,
              value: int = 0,
              data: Any = None,
              gas: int = 0,
              gas_price: int = 0,
              nonce: int = 0
              ) -> 'Sender':
        """
        构建交易详情
        Args:
            to_address: 接收地址
            value: 金额
            data: ABI数据包
            gas: gas
            gas_price: gas_price
            nonce: nonce
        Returns:
            交易发送者类
        """
        self._tx = self._contract.build_tx(self._wallet.address, to_address, value, data, gas_price, gas, nonce)
        return self

    def estimate_gas_fee(self) -> int:
        """
        估算gas费(单位Wei)
        Returns:
            gas
        """
        # 如果没有设置gas,则自动预估
        self._tx['gas'] = self._tx['gas'] or self._contract.estimate_tx_gas(self._tx)
        # 如果没有设置gas_price,则从链上中获取
        self._tx['gasPrice'] = self._tx['gasPrice'] or self._contract.w3.eth.gas_price

        return self._tx['gas'] * self._tx['gasPrice']

    def send(self):
        """
        发送交易
        Returns:
            交易哈希
        """
        # 如果gas为0,则计算gas
        if not self._tx["gas"]:
            self.estimate_gas_fee()
        # 发送交易
        return self._contract.send_tx(self._wallet.key, self._tx)
