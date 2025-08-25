from typing import Optional
import MetaTrader5 as mt5

def mt5_login(login: Optional[int] = None,
              password: Optional[str] = None,
              server: Optional[str] = None,
              path: Optional[str] = None,
              portable: bool = False) -> bool:
    """
    Initialize and (optionally) log in to MetaTrader 5.

    Args:
        login: Account number (int). If None, uses terminal's current session.
        password: Account password. Required if login is provided.
        server: Trade server name, e.g., 'MetaQuotes-Demo'.
        path: Full path to terminal (e.g., 'C:\\Program Files\\MetaTrader 5\\terminal64.exe').
        portable: Pass True if your terminal uses /portable mode.

    Returns:
        True if connected, False otherwise.
    """

    # Initialize (optionally with explicit terminal path)
    initialized = mt5.initialize(path=path, portable=portable) if path else mt5.initialize()
    if not initialized:
        print(f"MT5 initialize failed: {mt5.last_error()}" )
        return False

    # If login details are provided, perform login
    if login is not None:
        authorized = mt5.login(login=login, password=password, server=server)
        if not authorized:
            print(f"MT5 login failed: {mt5.last_error()}" )
            mt5.shutdown()
            return False

    # Basic terminal/account info
    info = mt5.terminal_info()
    acc  = mt5.account_info()
    if info:
        print(f"Terminal connected: {info.name} | build: {info.build}")
    if acc:
        print(f"Account: {acc.login} | Server: {acc.server} | Balance: {acc.balance}")
    return True