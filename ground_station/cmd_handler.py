import ast
import inspect
import re
from ground_station.hardware.naku_device_api import device


def get_available_methods():
    """_summary_

    Returns:
        _type_: _description_
    """
    return [{
                "module": getattr(device_module, 'api_name'),
                "doc": inspect.getdoc(getattr(device_module, func)),
                "method": func,
                'args': str(inspect.signature(getattr(device_module, func)))
            }
            for device_module in [device.rotator, device.radio] for func in dir(device_module)
            if callable(getattr(device_module, func)) and (func.startswith("set_") or func.startswith("get_") or
                                                           func.startswith("send"))]


available_methods = get_available_methods()


def get_help_string(argument=None, delimiter=' '):
    """_summary_

    Args:
        argument (_type_, optional): _description_. Defaults to None.
        delimiter (str, optional): _description_. Defaults to ' '.

    Returns:
        _type_: _description_
    """
    methods = available_methods
    help_string = f'Undefined function {argument}'
    if argument:
        for method in methods:
            if f"{method['module']}{delimiter}{method['method']}" == argument:
                help_string = f"{method['module']}{delimiter}{method['method']}{method['args']}\n{method['doc']}"
    else:
        help_string = 'There are available next methods:\n'
        help_string += '\n'.join([f"{method['module']}{delimiter}{method['method']}{method['args']}"
                                  for method in methods])
    return help_string


def cmd_handler(cmd_string: str, delimiter=' '):
    """_summary_

    Args:
        cmd_string (str): _description_
        delimiter (str, optional): _description_. Defaults to ' '.

    Returns:
        _type_: _description_
    """
    cmd_string = re.sub(' +', ' ', cmd_string).lstrip(' ')  # replace several spaces with one
    arg_string = re.search(r'\((.*?)\)', cmd_string)
    if arg_string:
        arg_string = arg_string.group(1)
    cmd = re.sub(r'\(.*?\)', '', cmd_string).rstrip(' ')

    if cmd.split(' ')[0] == 'help':
        return get_help_string(' '.join(cmd.split(' ')[1:]), delimiter)

    if cmd != '':
        # if cmd in available_methods:
        try:  # convert arg_string to kwargs and args
            kwargs = {}
            arg_list = []
            if arg_string is not None and arg_string != '':
                arg_list = [ast.literal_eval(arg) for arg in arg_string.split(', ') if '=' not in arg]
                _ = [kwargs.update(dict([arg.split("=")])) for arg in arg_string.split(', ') if '=' in arg]
        except (TypeError, SyntaxError):
            return 'Incorrect argument type'
        return execute_cmd(cmd, arg_list, kwargs)
        # else:
        #     return f'Undefined function {cmd}. See "help" for command list'
    else:
        return 'Enter any command. See "help" for command list'


def execute_cmd(cmd: str, args: list, kwargs: dict) -> str:
    """_summary_

    Args:
        cmd (str): _description_
        args (list): _description_
        kwargs (dict): _description_

    Returns:
        str: _description_
    """
    try:
        result = {}
        exec(f"""
try:
    if device.connection_status:
        exec_result = device.{cmd.replace(' ', '.')}(*{args}, **{kwargs})
    else:
        exec_result = "device is not connected"
except Exception as ex:
    exec_result = ex""", globals(), result)
        return result['exec_result']
    except Exception as err:
        return f'Error: {err}'

