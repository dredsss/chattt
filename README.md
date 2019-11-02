# chattt
ChatTT server is a simple chat IRC-like protocol on Python powered by JSON

## How it works
This protocol is working with JSON and non-blocking sockets. Each JSON request contains a "command" value and payload, applied to it. It could also be used in other purposes, like multiplayer games (if they don'y require too much data to be transported, otherwise it'll not be useful). ChatTT also supports modules to be run (each command is proceeded to module and it responses with granting or denying the command execution).

## How to add a module
First create a Python function (or a class method, it does not matter), then decide what commands will be processed by it, then add your function and expected commands to "modules" argument of Server instance. Format of it is included into the code as a comment.
Also you can use a module launcher. It's path is passed through 4th argument, it must include function called "get_module_list()", it must return a list of modules.

## How to run
Usage: python3 server.py <IP> <port> [module launcher path]
