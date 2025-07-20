# Signal Protocol Experiment

This is a simple implementation of the [Signal Protocol](https://signal.org/docs/specifications/doubleratchet/#introduction). 
This was made to better understand how the protocol works.

I make no guarantees of correct or secure implementation.
For a secure Version see Signals Implementation. 


## Installation

Use git to clone this repository.

```bash
pip install foobar
```

## Usage

This Project needs three different Terminals. 
One for the Server, one for 'Alice' and another one for 'Bob'

```
python3 server.py # starts the server
python3 user.py a # starts 'Alice'
python3 user.py b # starts 'Bob
```

## License

[MIT](https://choosealicense.com/licenses/mit/)