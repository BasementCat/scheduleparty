import functools
import argparse


commands = {}

def option(*args, **kwargs):
    def _option_outer_impl(callback):
        global commands
        commands.setdefault(callback.__name__, {'callback': callback, 'options': []})['options'].append((args, kwargs))
        return callback
    return _option_outer_impl

def command(callback):
    global commands
    commands.setdefault(callback.__name__, {'callback': callback, 'options': []})
    return callback

def run_command(args):
    parser = argparse.ArgumentParser()
    for a, ka in commands[args[1]]['options']:
        parser.add_argument(*a, **ka)
    command_args = vars(parser.parse_args(args[2:]))
    return commands[args[1]]['callback'](**command_args)
