For add-on descriptions, please see [DESCRIPTION.html](./DESCRIPTION.html). 
[AnkiWeb Link](https://ankiweb.net/shared/info/385888438)
# Development
## Setup
After cloning the project, run the following command
```
git submodule update --init --recursive
npm ci
```
The first command installs [ankiaddonconfig](https://github.com/BlueGreenMagick/ankiaddonconfig/) as a git submodule, and the second command installs the npm dev dependencies of this project.

## Updating typescript code

After editing code in [./src/ts](./src/ts), run `npx tsc` to compile it to [./src/addon/web/editor](./src/addon/web/editor).

## Tests & Formatting
This project uses [mypy](https://github.com/python/mypy) type checking for Python, and [standardjs](https://github.com/standard/standard) for formatting Javascript.

```
python -m mypy --no-strict-optional --disallow-untyped-defs .
npx standard --fix
```

You will need to install the following python packages to run mypy: 
```
python -m pip install aqt PyQt5-stubs mypy
```

This project doesn't use a strict python formatter. Even so, please make it look pretty enough :)

# Building ankiaddon file
After cloning the repo, go into the repo directory and run the following command to install the git submodule [ankiaddonconfig](https://github.com/BlueGreenMagick/ankiaddonconfig/)
```
git submodule update --init src/addon/ankiaddonconfig
```
After installing the git submodule, run the following command to create an `efdrc.ankiaddon` file
```
cd src/addon ; zip -r ../../efdrc.ankiaddon * ; cd ../../
```