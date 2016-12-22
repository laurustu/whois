# whois
Python parser for who.is, which parse whois tab to json file 

## Dependencies
Python 3.3+:
* requests
* bs4
* fake_useragent

## Usage
```bash
parse.py [-h] [-t] file
```
### Example:
```bash
parse.py list.txt
```
### Or:
```bash
parse.py list.txt -t
```
#### where:
`file` is a text file with domains line by line that are necessary to parse;

`-t` show additional messages with the time of each operation;

`-h` show help message.

### Text file example:
```
who.is
example.com
github.com
```
